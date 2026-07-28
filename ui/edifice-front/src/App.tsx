import { useEffect, useState } from "react";
import type { MissionContext, MissionSummary } from "./hal-types";
import { getMissionContext, listMissions } from "./mcp-data-adapter";
import { McpToolError, type ErrorCode } from "./cowork-mcp";
import { MissionList } from "./components/MissionList";
import { MissionDetail } from "./components/MissionDetail";
import { ErrorBanner } from "./components/ErrorBanner";

type LoadState =
  | { status: "loading" }
  | { status: "error"; code: ErrorCode; detail: string }
  | { status: "ready" };

export default function App() {
  const [missions, setMissions] = useState<MissionSummary[]>([]);
  const [listState, setListState] = useState<LoadState>({ status: "loading" });
  const [retriedOnce, setRetriedOnce] = useState(false);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [context, setContext] = useState<MissionContext | null>(null);
  const [detailState, setDetailState] = useState<LoadState | null>(null);

  async function loadMissions(isRetry = false) {
    if (isRetry) setRetriedOnce(true);
    setListState({ status: "loading" });
    try {
      const result = await listMissions();
      setMissions(result);
      setListState({ status: "ready" });
    } catch (err) {
      const code = err instanceof McpToolError ? err.code : "upstream_error";
      setListState({ status: "error", code, detail: err instanceof Error ? err.message : String(err) });
    }
  }

  useEffect(() => {
    void loadMissions();
  }, []);

  async function selectMission(missionId: string) {
    setSelectedId(missionId);
    setDetailState({ status: "loading" });
    try {
      const ctx = await getMissionContext(missionId);
      setContext(ctx);
      setDetailState({ status: "ready" });
    } catch (err) {
      const code = err instanceof McpToolError ? err.code : "upstream_error";
      setDetailState({ status: "error", code, detail: err instanceof Error ? err.message : String(err) });
    }
  }

  function backToList() {
    setSelectedId(null);
    setContext(null);
    setDetailState(null);
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="mb-4 text-lg font-semibold">Edifice — Missions</h1>

      {!selectedId && (
        <>
          {listState.status === "loading" && <p className="text-sm text-muted-foreground">Chargement des missions…</p>}
          {listState.status === "error" && (
            <ErrorBanner
              code={listState.code}
              detail={listState.detail}
              onRetry={retriedOnce ? undefined : () => loadMissions(true)}
            />
          )}
          {listState.status === "ready" && <MissionList missions={missions} onSelect={selectMission} />}
        </>
      )}

      {selectedId && detailState?.status === "loading" && (
        <p className="text-sm text-muted-foreground">Chargement de la mission…</p>
      )}
      {selectedId && detailState?.status === "error" && (
        <>
          <button type="button" onClick={backToList} className="mb-3 text-sm text-muted-foreground hover:underline">
            ← Retour aux missions
          </button>
          <ErrorBanner
            code={detailState.code}
            detail={detailState.detail}
            onRetry={() => void selectMission(selectedId)}
          />
        </>
      )}
      {selectedId && detailState?.status === "ready" && context && (
        <MissionDetail context={context} onBack={backToList} />
      )}
    </div>
  );
}
