/** Shared types for data_sync tool modules */

export type SyncMode = "full" | "incremental"
export type TriggerType = "manual" | "scheduled"
export type SyncStatus = "pending" | "running" | "success" | "failed"

export interface SyncTask {
  id: string
  entity_type: string
  sync_mode: SyncMode
  trigger_type: TriggerType
  status: SyncStatus
  started_at: string
  finished_at: string | null
  fetched_count: number | null
  created_count: number | null
  updated_count: number | null
  deleted_count: number | null
  error_message: string | null
  triggered_by_id: string | null
  created_at: string
}

export interface SyncTasksResponse {
  data: SyncTask[]
  count: number
}

export interface SyncStatusResponse {
  latest: SyncTask | null
  is_running: boolean
  next_incremental_sync: string | null
  next_full_sync: string | null
}

export interface TriggerRequest {
  mode: SyncMode
}

// ─── Synced entity types ────────────────────────────────────────────────────

export interface WecomDepartment {
  id: number
  name: string
  name_en: string | null
  parentid: number | null
  order: number
  synced_at: string
}

export interface WecomMember {
  userid: string
  name: string
  is_active: boolean
  created_at: string | null
}

export interface WecomDepartmentsResponse {
  data: WecomDepartment[]
  count: number
}

export interface WecomMembersResponse {
  data: WecomMember[]
  count: number
}
