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
let resolvedWorkspaceDir: string | undefined;

const pluginRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

/**
 * Resolve the canonical handbook directory.
 * Priority: pluginCfg.handbookDir (checked by caller) > workspaceDir/handbook > cwd/handbook
 */
function resolveHandbookDir(fallback?: string): string {
	return fallback || path.join(process.cwd(), "handbook");
}

function bootstrapHandbook(handbookDir: string) {
	const dirs = [
		"inbox/assignments",
		"inbox/archive",
		"projects",
		"feedback",
		"scripts/task-kit",
	];
	for (const d of dirs) {
		fs.mkdirSync(path.join(handbookDir, d), { recursive: true });
	}
}

function installScripts(handbookDir: string) {
	const srcDir = path.join(pluginRoot, "scripts", "task-kit");
	if (!fs.existsSync(srcDir)) return;

	bootstrapHandbook(handbookDir);

	const destDir = path.join(handbookDir, "scripts", "task-kit");
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

const PRIORITY_ORDER: Record<string, number> = { high: 0, normal: 1, low: 2 };

type Assignment = {
	id: string;
	to: string;
	from?: string;
	project?: string;
	task_path?: string;
	priority?: string;
	status?: string;
	summary?: string;
	body?: string;
	filePath: string;
};

function parseFrontmatter(raw: string): { fields: Record<string, string>; body: string } {
	const m = raw.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)/);
	if (!m) return { fields: {}, body: raw.trim() };
	const fields: Record<string, string> = {};
	for (const line of m[1].split("\n")) {
		const idx = line.indexOf(":");
		if (idx <= 0) continue;
		const k = line.slice(0, idx).trim();
		const v = line.slice(idx + 1).trim();
		if (k) fields[k] = v;
	}
	return { fields, body: (m[2] ?? "").trim() };
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
			const { fields: fm, body } = parseFrontmatter(raw);
			result.push({
				id: fm.id || path.basename(f, ".md"),
				to: fm.to || "",
				from: fm.from,
				project: fm.project,
				task_path: fm.task_path,
				priority: fm.priority,
				status: fm.status || "assigned",
				summary: fm.summary,
				body: body || undefined,
				filePath,
			});
		} catch {
			// Ignore malformed files and continue.
		}
	}
	return result;
}

function loadTaskContent(taskPath: string, handbookDir: string): string | undefined {
	// task_path may be relative to handbook root or absolute
	const resolved = path.isAbsolute(taskPath) ? taskPath : path.join(handbookDir, taskPath);
	try {
		if (!fs.existsSync(resolved)) return undefined;
		const raw = fs.readFileSync(resolved, "utf-8");
		// Strip frontmatter, return body only
		return raw.replace(/^---\n[\s\S]*?\n---\n?/, "").trim() || undefined;
	} catch {
		return undefined;
	}
}

function formatAssignments(assignments: Assignment[], handbookDir: string): string {
	const sections = ["[Inbox Assignments]"];
	for (const a of assignments) {
		const isHigh = a.priority === "high";
		const tag = isHigh ? "[!HIGH] " : "";
		const header = `### ${tag}${a.id} (from=${a.from ?? "unknown"} | project=${a.project ?? ""} | priority=${a.priority ?? "normal"})`;
		const lines = [header];
		if (a.summary) lines.push(`**Summary**: ${a.summary}`);

		// Include assignment body (## Context / ## Acceptance etc.)
		if (a.body) lines.push("", a.body);

		// Include linked task.md content
		if (a.task_path) {
			const taskContent = loadTaskContent(a.task_path, handbookDir);
			if (taskContent) {
				lines.push("", "#### Linked Task Detail", "", taskContent);
			}
		}

		sections.push(lines.join("\n"));
	}
	sections.push("\nUse these assignments as high-priority execution context.");
	return sections.join("\n\n");
}

/** Frontmatter keys surfaced in the injected project context header. */
const PROJECT_META_KEYS = ["source", "repo", "npm", "linear_team", "github_org"] as const;

function loadProjectContexts(handbookDir: string, projectSlugs: Set<string>): string | undefined {
	if (projectSlugs.size === 0) return undefined;
	const projectsDir = path.join(handbookDir, "projects");
	if (!fs.existsSync(projectsDir)) return undefined;

	const sections: string[] = [];
	for (const proj of projectSlugs) {
		const contextPath = path.join(projectsDir, proj, "context.md");
		if (!fs.existsSync(contextPath)) continue;
		try {
			const raw = fs.readFileSync(contextPath, "utf-8");
			const { fields, body } = parseFrontmatter(raw);

			// Surface key metadata so agents know where the project lives.
			const meta = PROJECT_META_KEYS.filter((k) => fields[k])
				.map((k) => `${k}: ${fields[k]}`)
				.join(" | ");
			const header = meta ? `[Project: ${proj}] (${meta})` : `[Project: ${proj}]`;

			if (body) sections.push(`${header}\n${body}`);
		} catch {
			// Ignore read errors.
		}
	}

	return sections.length > 0 ? sections.join("\n\n") : undefined;
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

		const defaultHandbookDir = pluginCfg.handbookDir || resolveHandbookDir();
		try {
			installScripts(defaultHandbookDir);
		} catch (err) {
			api.logger.warn?.(`[oh-my-openclaw] failed to install scripts: ${err}`);
		}

		// Hook 1: inject assignment context
		api.on("before_prompt_build", async (_event, ctx) => {
			if (ctx.workspaceDir) resolvedWorkspaceDir = ctx.workspaceDir;

			const agentId = (ctx.agentId ?? "").trim();
			if (!agentId) return undefined;

			const onlyAgents = Array.isArray(pluginCfg.onlyAgents)
				? pluginCfg.onlyAgents.map((x) => String(x).trim()).filter(Boolean)
				: [];
			if (onlyAgents.length > 0 && !onlyAgents.includes(agentId)) {
				return undefined;
			}
			const handbookDir = pluginCfg.handbookDir || resolveHandbookDir(ctx.workspaceDir ? path.join(ctx.workspaceDir, "handbook") : undefined);
			const assignmentsDir =
				pluginCfg.assignmentsDir || path.join(handbookDir, "inbox", "assignments");
			const maxAssignments = Math.max(1, Math.min(50, Number(pluginCfg.maxAssignments || 10)));

			const assignments = loadAssignments(assignmentsDir)
				.filter((a) => a.to === agentId && (a.status ?? "assigned") === "assigned")
				.sort((a, b) =>
					(PRIORITY_ORDER[a.priority ?? "normal"] ?? 1) -
					(PRIORITY_ORDER[b.priority ?? "normal"] ?? 1)
				)
				.slice(0, maxAssignments);

			// Collect project slugs from this agent's assignments for filtered context loading
			const projectSlugs = new Set<string>();
			for (const a of assignments) {
				if (a.project) projectSlugs.add(a.project);
			}

			const parts: string[] = [];
			const projectContext = loadProjectContexts(handbookDir, projectSlugs);
			if (projectContext) parts.push(projectContext);
			if (assignments.length > 0) parts.push(formatAssignments(assignments, handbookDir));

			if (parts.length === 0) return undefined;

			const prependContext = parts.join("\n\n");
			api.logger.info?.(
				`[inbox-assistant] injected context for agent=${agentId}: ${assignments.length} assignment(s), projects=${projectContext ? "yes" : "no"}`,
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

				const workspaceDir = resolvedWorkspaceDir || process.cwd();
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
