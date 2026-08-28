/** Raw shapes returned by hal-mcp's Edifice tools — mirrors the live schemas, not guessed. */

export interface MissionSummary {
  id: string;
  name: string;
  type: string;
  status: string;
  mission_context: string | null;
  created_at: string;
  building: { name: string; address: string } | null;
}

/** list_edifice_missions response since hal#119 — a bare array no longer comes back. */
export interface MissionListEnvelope {
  missions: MissionSummary[];
  total: number;
  returned: number;
  truncated: boolean;
}

export interface RawNote {
  note_id: string;
  type: string;
  name: string;
  description: string;
  photos: string[];
  photo: string;
  metadata: Record<string, unknown> | null;
}

export interface RawObservation {
  note_id: string;
  ref?: string;
  name?: string;
  zone?: string;
  location?: string;
  description?: string;
  assessment?: string | null;
  recommendations?: string;
  metadata?: Record<string, unknown> | null;
}

export interface RawPhoto {
  id: string;
  original_filename: string;
  storage_path: string;
  note_id: string | null;
  crop_region: { x: number; y: number; width: number; height: number } | null;
  created_at: string;
  annotations: unknown[];
}

/** get_mission_context response shape (== the local context.json contract). */
export interface MissionContext {
  project_type: string;
  building_id: string | null;
  titre_service: string;
  client: string;
  residence: string;
  adresse: string;
  date_visite: string;
  description_batiment: string;
  objet_visite: string;
  synthese: string;
  conclusion: string;
  observations: RawObservation[];
  notes: RawNote[];
  photos: RawPhoto[];
}
