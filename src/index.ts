import fs from "node:fs";
import path from "node:path";
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { emptyPluginConfigSchema } from "openclaw/plugin-sdk";
import manifest from "../openclaw.plugin.json" with { type: "json" };

type SessionSnapshot = {
	agentId: string;
	sessionId: string;
	messages: Array<{ role: string; content: unknown }>;
	updatedAt: number;
};

const sessionCache = new Map<string, SessionSnapshot>();

const pluginRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

function installScripts(handbookDir: string) {
	const srcDir = path.join(pluginRoot, "scripts", "task-kit");
	if (!fs.existsSync(srcDir)) return;

	const destDir = path.join(handbookDir, "scripts", "task-kit");
	fs.mkdirSync(destDir, { recursive: true });

	for (const file of fs.readdirSync(srcDir)) {
		const src = path.join(srcDir, file);
		const dest = path.join(destDir, file);
		if (fs.existsSync(dest)) continue;
		fs.copyFileSync(src, dest);
	}
}

function extractTextContent(content: unknown): string {
	if (typeof content === "string") return content;
	if (Array.isArray(content)) {
		return content
			.filter(
				(p): p is { type: string; text: string } =>
					typeof p === "object" && p !== null && p.type === "text" && typeof p.text === "string",
			)
			.map((p) => p.text)
			.join("\n");
	}
	return "";
}

type Assignment = {
	id: string;
	to: string;
	from?: string;
	project?: string;
	task_path?: string;
	priority?: string;
	status?: string;
	summary?: string;
	filePath: string;
};

function parseFrontmatter(raw: string): Record<string, string> {
	const m = raw.match(/^---\n([\s\S]*?)\n---\n?/);
	if (!m) return {};
	const out: Record<string, string> = {};
	for (const line of m[1].split("\n")) {
		const idx = line.indexOf(":");
		if (idx <= 0) continue;
		const k = line.slice(0, idx).trim();
		const v = line.slice(idx + 1).trim();
		if (k) out[k] = v;
	}
	return out;
}

function loadAssignments(assignmentsDir: string): Assignment[] {
	if (!fs.existsSync(assignmentsDir)) return [];
	const files = fs
		.readdirSync(assignmentsDir)
		.filter((f) => f.endsWith(".md"))
		.sort();

	const result: Assignment[] = [];
	for (const f of files) {
		const filePath = path.join(assignmentsDir, f);
		try {
			const raw = fs.readFileSync(filePath, "utf-8");
			const fm = parseFrontmatter(raw);
			result.push({
				id: fm.id || path.basename(f, ".md"),
				to: fm.to || "",
				from: fm.from,
				project: fm.project,
				task_path: fm.task_path,
				priority: fm.priority,
				status: fm.status || "assigned",
				summary: fm.summary,
				filePath,
			});
		} catch {
			// Ignore malformed files and continue.
		}
	}
	return result;
}

function formatAssignments(assignments: Assignment[]): string {
	const lines = ["[Inbox Assignments]"];
	for (const a of assignments) {
		lines.push(
			`- id=${a.id} | from=${a.from ?? "unknown"} | project=${a.project ?? ""} | priority=${a.priority ?? "normal"}`,
		);
		if (a.task_path) lines.push(`  task_path: ${a.task_path}`);
		if (a.summary) lines.push(`  summary: ${a.summary}`);
	}
	lines.push("Use these assignments as high-priority execution context.");
	return lines.join("\n");
}

const plugin = {
	id: manifest.id,
	name: manifest.name,
	description: manifest.description,
	configSchema: emptyPluginConfigSchema(),
	register(api: OpenClawPluginApi) {
		const pluginCfg = (api.pluginConfig ?? {}) as {
			handbookDir?: string;
			assignmentsDir?: string;
			maxAssignments?: number;
			onlyAgents?: string[];
			feedbackDir?: string;
			maxContextMessages?: number;
		};

		// Hook 1: inject assignment context + install scripts on first call
		api.on("before_prompt_build", async (_event, ctx) => {
			const workspaceDir = ctx.workspaceDir || process.cwd();
			const handbookDir = pluginCfg.handbookDir || path.join(workspaceDir, "handbook");

			try {
				installScripts(handbookDir);
			} catch (err) {
				api.logger.warn?.(`[oh-my-openclaw] failed to install scripts: ${err}`);
			}

			const agentId = (ctx.agentId ?? "").trim();
			if (!agentId) return undefined;

			const onlyAgents = Array.isArray(pluginCfg.onlyAgents)
				? pluginCfg.onlyAgents.map((x) => String(x).trim()).filter(Boolean)
				: [];
			if (onlyAgents.length > 0 && !onlyAgents.includes(agentId)) {
				return undefined;
			}
			const assignmentsDir =
				pluginCfg.assignmentsDir || path.join(handbookDir, "inbox", "assignments");
			const maxAssignments = Math.max(1, Math.min(20, Number(pluginCfg.maxAssignments || 3)));

			const assignments = loadAssignments(assignmentsDir)
				.filter((a) => a.to === agentId && (a.status ?? "assigned") === "assigned")
				.slice(0, maxAssignments);

			if (assignments.length === 0) return undefined;

			const prependContext = formatAssignments(assignments);
			api.logger.info?.(
				`[inbox-assistant] injected ${assignments.length} assignment(s) for agent=${agentId}`,
			);
			return { prependContext };
		});

		// Hook 2: cache user/assistant messages for feedback command
		api.on("before_prompt_build", (event, ctx) => {
			const agentId = (ctx.agentId ?? "").trim();
			if (!agentId) return;
			const msgs = (event.messages ?? []) as Array<{
				role?: string;
				content?: unknown;
			}>;
			const filtered = msgs.filter((m) => m.role === "user" || m.role === "assistant");
			const max = Math.max(1, Math.min(50, Number(pluginCfg.maxContextMessages || 20)));
			sessionCache.set(agentId, {
				agentId,
				sessionId: ctx.sessionId ?? "",
				messages: filtered.slice(-max) as Array<{
					role: string;
					content: unknown;
				}>,
				updatedAt: Date.now(),
			});
		});

		// Command: /fb
		api.registerCommand({
			name: "fb",
			description: "Save feedback with recent conversation context",
			acceptsArgs: true,
			requireAuth: true,
			handler: async (cmdCtx) => {
				const text = cmdCtx.args?.trim();
				if (!text) return { text: "Usage: /fb <your feedback>" };

				let best: SessionSnapshot | undefined;
				for (const snap of sessionCache.values()) {
					if (!best || snap.updatedAt > best.updatedAt) best = snap;
				}

				const lines: string[] = [];
				if (best) {
					for (const m of best.messages) {
						const content = extractTextContent(m.content);
						if (content) lines.push(`[${m.role}] ${content}`);
					}
				}

				const workspaceDir = process.cwd();
				const handbookDir = pluginCfg.handbookDir || path.join(workspaceDir, "handbook");
				const feedbackDir = pluginCfg.feedbackDir || path.join(handbookDir, "feedback");
				fs.mkdirSync(feedbackDir, { recursive: true });
				const ts = new Date().toISOString().slice(0, 16).replace(/[:.]/g, "-");
				const filePath = path.join(feedbackDir, `${ts}.md`);
				const md = [
					"---",
					`created_at: ${new Date().toISOString()}`,
					`agent: ${best?.agentId ?? "unknown"}`,
					`session: ${best?.sessionId ?? "unknown"}`,
					`channel: ${cmdCtx.channel}`,
					`from: ${cmdCtx.senderId ?? "unknown"}`,
					"---",
					"",
					"## Feedback",
					"",
					text,
					"",
					"## Conversation Context",
					"",
					lines.join("\n\n"),
				].join("\n");
				fs.writeFileSync(filePath, md, "utf-8");

				api.logger.info?.(`[inbox-assistant] feedback saved → ${filePath}`);
				return { text: `Feedback saved → ${path.basename(filePath)}` };
			},
		});
	},
};

export default plugin;
