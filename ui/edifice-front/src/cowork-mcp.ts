/**
 * window.cowork.callMcpTool wrapper — the artifact's only I/O channel.
 * Tool names are resolved from the artifact's own meta block at runtime
 * (never hardcoded), so the committed build carries no server UUID; the
 * skill route hydrates only the meta block's JSON, not this bundle.
 */

export type ErrorCode =
  | "no_cowork"
  | "bad_meta"
  | "needs_reauth"
  | "server_not_connected"
  | "server_unavailable"
  | "upstream_error";

export class McpToolError extends Error {
  code: ErrorCode;
  constructor(code: ErrorCode, message: string) {
    super(message);
    this.name = "McpToolError";
    this.code = code;
  }
}

type ToolShortName = "list_edifice_missions" | "get_mission_context" | "get_mission_photo";

interface CoworkArtifactMeta {
  name?: string;
  mcpTools: string[];
  mcpServerNames: string[];
}

declare global {
  interface Window {
    cowork?: {
      callMcpTool: (name: string, args?: Record<string, unknown>) => Promise<McpToolResult>;
    };
  }
}

interface McpImageContent {
  type: "image";
  data: string;
  mimeType: string;
}

interface McpTextContent {
  type: "text";
  text: string;
}

type McpContent = McpImageContent | McpTextContent;

interface McpToolResult {
  isError?: boolean;
  content?: McpContent[];
  structuredContent?: unknown;
}

let cachedMeta: CoworkArtifactMeta | null = null;

function readMeta(): CoworkArtifactMeta {
  if (cachedMeta) return cachedMeta;
  const el = document.getElementById("cowork-artifact-meta");
  if (!el || !el.textContent) {
    throw new McpToolError("bad_meta", "Bloc meta cowork-artifact-meta introuvable dans ce document.");
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(el.textContent);
  } catch (err) {
    throw new McpToolError("bad_meta", `Bloc meta illisible (JSON invalide) : ${String(err)}`);
  }
  cachedMeta = parsed as CoworkArtifactMeta;
  return cachedMeta;
}

/**
 * Resolves a short tool name to the full `mcp__<uuid>__<tool>` id declared in the
 * meta block. On failure the message reports which artifact is running and what
 * the block actually declares — a mismatch here means the open artifact is a
 * stale copy or was never hydrated, and only the real values tell them apart.
 */
function resolveToolName(shortName: ToolShortName): string {
  const meta = readMeta();
  const declared = Array.isArray(meta.mcpTools) ? meta.mcpTools : [];
  const full = declared.find((t) => t.endsWith(`__${shortName}`));
  if (!full) {
    const artifact = meta.name ? `"${meta.name}"` : "(sans nom)";
    const list = declared.length
      ? declared.map((t) => `"${t}"`).join(", ")
      : Array.isArray(meta.mcpTools)
        ? "liste vide"
        : "champ mcpTools absent ou non-tableau";
    throw new McpToolError(
      "bad_meta",
      `Outil "${shortName}" introuvable dans le bloc meta de l'artefact ${artifact}. ` +
        `mcpTools déclare : ${list}. Un id complet ressemble à ` +
        `"mcp__<uuid-connecteur>__${shortName}".`,
    );
  }
  return full;
}

/**
 * Best-effort classification of a cowork.callMcpTool failure. The exact
 * error string shapes Cowork surfaces for each failure mode are not
 * documented publicly — this heuristic is unverified against a live
 * session and should be checked against real error text.
 * TODO: verify in Cowork — exact error message shapes per failure mode.
 */
function classifyError(raw: string): ErrorCode {
  const s = raw.toLowerCase();
  if (s.includes("reauth") || s.includes("authenticate") || s.includes("unauthorized")) {
    return "needs_reauth";
  }
  if (s.includes("not connected") || s.includes("no connector") || s.includes("not found")) {
    return "server_not_connected";
  }
  if (s.includes("timeout") || s.includes("unavailable") || s.includes("network")) {
    return "server_unavailable";
  }
  return "upstream_error";
}

function extractText(result: McpToolResult): string | null {
  const block = result.content?.find((c): c is McpTextContent => c.type === "text");
  return block ? block.text : null;
}

function extractImage(result: McpToolResult): McpImageContent | null {
  const block = result.content?.find((c): c is McpImageContent => c.type === "image");
  return block ?? null;
}

/** Calls a JSON-returning tool (list_edifice_missions, get_mission_context). */
export async function callJsonTool<T>(
  shortName: Extract<ToolShortName, "list_edifice_missions" | "get_mission_context">,
  args: Record<string, unknown> = {},
): Promise<T> {
  if (!window.cowork?.callMcpTool) {
    throw new McpToolError("no_cowork", "window.cowork indisponible — cet artefact ne fonctionne que dans Claude Cowork.");
  }
  const fullName = resolveToolName(shortName);
  let result: McpToolResult;
  try {
    result = await window.cowork.callMcpTool(fullName, args);
  } catch (err) {
    throw new McpToolError(classifyError(String(err)), String(err));
  }
  if (result.isError) {
    const text = extractText(result) ?? "Erreur outil MCP inconnue";
    throw new McpToolError(classifyError(text), text);
  }
  if (result.structuredContent != null) return result.structuredContent as T;
  const text = extractText(result);
  if (text != null) {
    try {
      return JSON.parse(text) as T;
    } catch {
      throw new McpToolError("upstream_error", `Réponse non-JSON de ${shortName}: ${text}`);
    }
  }
  throw new McpToolError("upstream_error", `Réponse vide de ${shortName}`);
}

/** Calls get_mission_photo and returns a data: URI (never a network URL). */
export async function callPhotoTool(
  photoId: string,
  maxWidth?: number,
): Promise<string> {
  if (!window.cowork?.callMcpTool) {
    throw new McpToolError("no_cowork", "window.cowork indisponible — cet artefact ne fonctionne que dans Claude Cowork.");
  }
  const fullName = resolveToolName("get_mission_photo");
  const args: Record<string, unknown> = { photo_id: photoId };
  if (maxWidth) args.max_width = maxWidth;
  let result: McpToolResult;
  try {
    result = await window.cowork.callMcpTool(fullName, args);
  } catch (err) {
    throw new McpToolError(classifyError(String(err)), String(err));
  }
  if (result.isError) {
    const text = extractText(result) ?? "Erreur outil MCP inconnue";
    throw new McpToolError(classifyError(text), text);
  }
  const image = extractImage(result);
  if (!image) {
    throw new McpToolError("upstream_error", `get_mission_photo n'a renvoyé aucune image pour ${photoId}`);
  }
  return `data:${image.mimeType};base64,${image.data}`;
}
