import { useState } from "react";
import { PhotoGallery } from "@bluegreeno/annotation-core";
import type { MissionContext } from "../hal-types";
import { resolveGalleryPhotos, toNoteWithRelations, type GalleryPhoto } from "../mcp-data-adapter";
import { ErrorBanner } from "./ErrorBanner";
import { McpToolError, type ErrorCode } from "../cowork-mcp";

type Tab = "infos" | "notes" | "photos";

export function MissionDetail({
  context,
  onBack,
}: {
  context: MissionContext;
  onBack: () => void;
}) {
  const [tab, setTab] = useState<Tab>("infos");
  const [photos, setPhotos] = useState<GalleryPhoto[] | null>(null);
  const [photosLoading, setPhotosLoading] = useState(false);
  const [photosError, setPhotosError] = useState<{ code: ErrorCode; detail: string } | null>(null);
  const [retriedOnce, setRetriedOnce] = useState(false);

  const notes = toNoteWithRelations(context);

  async function loadPhotos(isRetry = false) {
    if (isRetry) setRetriedOnce(true);
    setPhotosLoading(true);
    setPhotosError(null);
    try {
      const resolved = await resolveGalleryPhotos(context.photos, context.building_id);
      setPhotos(resolved);
    } catch (err) {
      const code = err instanceof McpToolError ? err.code : "upstream_error";
      setPhotosError({ code, detail: err instanceof Error ? err.message : String(err) });
    } finally {
      setPhotosLoading(false);
    }
  }

  function selectTab(next: Tab) {
    setTab(next);
    if (next === "photos" && photos === null && !photosLoading) {
      void loadPhotos();
    }
  }

  return (
    <div className="space-y-4">
      <button type="button" onClick={onBack} className="text-sm text-muted-foreground hover:underline">
        ← Retour aux missions
      </button>

      <h1 className="text-xl font-semibold">{context.titre_service || context.residence}</h1>
      <p className="text-sm text-muted-foreground">{context.adresse}</p>

      <div className="flex gap-4 border-b">
        {(["infos", "notes", "photos"] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => selectTab(t)}
            className={`px-1 pb-2 text-sm capitalize ${
              tab === t ? "border-b-2 border-primary font-medium" : "text-muted-foreground"
            }`}
          >
            {t === "infos" ? "Infos" : t === "notes" ? `Notes (${notes.length})` : `Photos (${context.photos.length})`}
          </button>
        ))}
      </div>

      {tab === "infos" && (
        <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-2 text-sm">
          <dt className="text-muted-foreground">Type</dt>
          <dd className="select-text">{context.project_type}</dd>
          <dt className="text-muted-foreground">Date de visite</dt>
          <dd className="select-text">{context.date_visite || "—"}</dd>
          <dt className="text-muted-foreground">Description du bâtiment</dt>
          <dd className="select-text">{context.description_batiment || "—"}</dd>
          <dt className="text-muted-foreground">Objet de la visite</dt>
          <dd className="select-text">{context.objet_visite || "—"}</dd>
          <dt className="text-muted-foreground">Synthèse</dt>
          <dd className="select-text">{context.synthese || "—"}</dd>
        </dl>
      )}

      {tab === "notes" && (
        <ul className="space-y-3">
          {notes.length === 0 && <p className="text-sm text-muted-foreground">Aucune note.</p>}
          {notes.map((n) => (
            <li key={n.id} className="rounded-lg border p-3">
              <p className="font-medium">{n.name}</p>
              <p className="select-text mt-1 text-sm text-muted-foreground">{n.description || "—"}</p>
            </li>
          ))}
        </ul>
      )}

      {tab === "photos" && (
        <>
          {photosLoading && <p className="text-sm text-muted-foreground">Chargement des photos…</p>}
          {photosError && (
            <ErrorBanner
              code={photosError.code}
              detail={photosError.detail}
              onRetry={retriedOnce ? undefined : () => loadPhotos(true)}
            />
          )}
          {photos && !photosLoading && <PhotoGallery photos={photos} />}
        </>
      )}
    </div>
  );
}
