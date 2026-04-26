export type ExportedFilter = "all" | "exported" | "not_exported"

export interface InvoiceFileBriefPublic {
  id: string
  invoice_number: string
  invoice_date: string
  invoice_amount: string
  currency: string
  seller: string
}

export interface PurchaseRecordWithExportInfo {
  id: string
  owner_id: string
  purchase_date: string
  amount: string
  currency: string
  order_name: string
  category: string
  subcategory: string | null
  note: string | null
  status: string
  created_at: string | null
  invoice_file: InvoiceFileBriefPublic | null
  exported: boolean
  latest_exported_at: string | null
  latest_exported_by: string | null
}

export interface RecordsPublic {
  data: PurchaseRecordWithExportInfo[]
  count: number
}

export interface RecordsQuery {
  skip?: number
  limit?: number
  start_date?: string
  end_date?: string
  category?: string
  subcategory?: string
  currency?: string
  owner_id?: string
  exported?: ExportedFilter
  q?: string
  [key: string]: unknown
}

export interface ReimbursementExportItemPublic {
  id: string
  export_id: string
  purchase_record_id: string
  invoice_file_id: string | null
  invoice_match_id: string | null
  document_number: number
  purchase_date: string
  amount: string
  currency: string
  category: string
  subcategory: string | null
  order_name: string
  remark: string | null
  description_snapshot: string | null
  department_snapshot: string | null
  created_at: string
}

export interface ReimbursementExportPublic {
  id: string
  created_by_id: string
  created_at: string
  department: string | null
  business_unit: string | null
  reimburser: string | null
  reimbursement_date: string | null
  currency: string | null
  total_amount: string
  item_count: number
  original_filename: string | null
  stored_filename: string | null
  file_path: string | null
  mime_type: string | null
  file_size: number | null
  file_expires_at: string | null
  file_deleted_at: string | null
}

export interface ReimbursementExportDetailPublic
  extends ReimbursementExportPublic {
  items: ReimbursementExportItemPublic[]
}

export interface ReimbursementExportsPublic {
  data: ReimbursementExportPublic[]
  count: number
}

export interface GenerateRequest {
  purchase_record_ids: string[]
  department?: string | null
  business_unit?: string | null
  reimburser?: string | null
  reimbursement_date?: string | null
  retention_days?: number | null
}

export interface SettingsResponse {
  retention_days: number
}

export interface SettingsUpdate {
  retention_days?: number | null
}

export interface PurgeResult {
  purged_count: number
  purged_ids: string[]
}
