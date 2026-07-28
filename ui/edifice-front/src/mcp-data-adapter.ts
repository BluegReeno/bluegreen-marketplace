import { callJsonTool, callPhotoTool } from "./cowork-mcp";
import type { MissionContext, MissionSummary, RawPhoto } from "./hal-types";
import type { AnnotationPhoto, Json, NoteWithRelations } from "@bluegreeno/annotation-core";

export function listMissions(status?: string, limit?: number): Promise<MissionSummary[]> {
  const args: Record<string, unknown> = {};
  if (status) args.status = status;
  if (limit) args.limit = limit;
  return callJsonTool<MissionSummary[]>("list_edifice_missions", args);
}

export function getMissionContext(missionId: string): Promise<MissionContext> {
  return callJsonTool<MissionContext>("get_mission_context", { mission_id: missionId });
}

/** Gallery thumbnail/viewer resolution — one tier, balancing legibility and payload size. */
const PHOTO_MAX_WIDTH = 600;

export type GalleryPhoto = AnnotationPhoto & { signedUrl: string; annotationCount?: number };

/**
 * Resolves every photo of a mission to a data: URI via get_mission_photo, in
 * parallel. Each call is a read-only tool (readOnlyHint per hal#82) — the
 * permission-cascade risk on load-time (non-click-triggered) calls is a known
 * unverified item, see docs/artifact-front-ends.md and issue #50.
 * TODO: verify in Cowork — does this trigger more than the "at most one
 * permission dialog on open" acceptance criterion in practice?
 */
export async function resolveGalleryPhotos(
  photos: RawPhoto[],
  buildingId: string | null,
): Promise<GalleryPhoto[]> {
  const results = await Promise.all(
    photos.map(async (p): Promise<GalleryPhoto> => {
      const signedUrl = await callPhotoTool(p.id, PHOTO_MAX_WIDTH);
      return {
        id: p.id,
        project_id: buildingId ?? "",
        storage_path: p.storage_path,
        width: 0,
        height: 0,
        caption: null,
        category: null,
        created_at: p.created_at,
        crop_region: p.crop_region as unknown as Json | null,
        exif_data: null,
        file_size: null,
        message_id: null,
        mime_type: "image/jpeg",
        note_id: p.note_id,
        original_filename: p.original_filename,
        roboflow_image_id: null,
        roboflow_sync_status: null,
        rotation: 0,
        updated_at: null,
        uploaded_by: null,
        signedUrl,
        annotationCount: p.annotations?.length ?? 0,
      };
    }),
  );
  return results;
}

export function toNoteWithRelations(context: MissionContext): NoteWithRelations[] {
  return context.notes.map((note) => ({
    id: note.note_id,
    name: note.name,
    project_id: context.building_id ?? "",
    assessment: null,
    cause: null,
    component_type_id: null,
    created_at: null,
    created_by: null,
    description: note.description,
    disorder_type_id: null,
    display_order: null,
    element: null,
    location: null,
    metadata: note.metadata as unknown as Json | null,
    recommendations: null,
    ref: null,
    type: note.type,
    updated_at: null,
    zone: null,
    edifice_component_types: null,
    edifice_disorder_types: null,
  }));
}
