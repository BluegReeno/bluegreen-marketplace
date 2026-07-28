import type { ErrorCode } from "../cowork-mcp";

const MESSAGES: Record<ErrorCode, { title: string; hint: string; retryable: boolean }> = {
  no_cowork: {
    title: "Cet artefact ne fonctionne que dans Claude Cowork.",
    hint: "Ouvrez-le depuis une session Cowork avec le connecteur hal-mcp activé.",
    retryable: false,
  },
  needs_reauth: {
    title: "Connexion hal-mcp expirée.",
    hint: "Ré-autorisez le connecteur hal-mcp dans les réglages Cowork, puis rouvrez cet artefact.",
    retryable: false,
  },
  server_not_connected: {
    title: "hal-mcp n'est pas connecté.",
    hint: "Activez le connecteur hal-mcp dans les réglages Cowork, puis rouvrez cet artefact.",
    retryable: false,
  },
  server_unavailable: {
    title: "hal-mcp est temporairement indisponible.",
    hint: "Le serveur ne répond pas — réessayez.",
    retryable: true,
  },
  upstream_error: {
    title: "Erreur hal-mcp.",
    hint: "Une erreur inattendue est survenue côté serveur.",
    retryable: false,
  },
};

export function ErrorBanner({
  code,
  detail,
  onRetry,
}: {
  code: ErrorCode;
  detail: string;
  onRetry?: () => void;
}) {
  const { title, hint, retryable } = MESSAGES[code];
  return (
    <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
      <p className="font-semibold">{title}</p>
      <p className="mt-1 text-sm">{hint}</p>
      <p className="mt-2 select-text text-xs opacity-70">{detail}</p>
      {retryable && onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-md border border-destructive/50 px-3 py-1 text-sm hover:bg-destructive/10"
        >
          Réessayer
        </button>
      )}
    </div>
  );
}
