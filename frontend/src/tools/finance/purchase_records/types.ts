export interface PurchaseRecord {
  id: string
  owner_id: string
  purchase_date: string
  amount: string
  currency: string
  order_name: string
  category: string
  subcategory: string | null
  note: string | null
  status: "draft" | "submitted" | "approved" | "rejected"
  invoice_match_status: "unmatched" | "matched"
  screenshot_path: string
  screenshot_original_name: string
  screenshot_mime_type: string
  screenshot_size: number
  deleted_at: string | null
  deleted_by_id: string | null
  created_at: string
  updated_at: string | null
}

export interface PurchaseRecordCreate {
  purchase_date: string
  amount: string
  currency: string
  order_name: string
  category: string
  subcategory?: string | null
  note?: string | null
  screenshot: File
}

export interface PurchaseRecordUpdate {
  purchase_date?: string
  amount?: string
  currency?: string
  order_name?: string
  category?: string
  subcategory?: string | null
  note?: string | null
  screenshot?: File
}

export interface PurchaseRecordListResponse {
  data: PurchaseRecord[]
  count: number
}

export interface OcrPreviewResponse {
  purchase_date: string | null
  amount: string | null
  currency: string | null
  order_name: string | null
  category: string | null
  subcategory: string | null
  note: string | null
}

export interface RejectRequest {
  reason: string
}
