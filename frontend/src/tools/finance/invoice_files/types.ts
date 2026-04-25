export interface InvoiceFile {
  id: string
  owner_id: string
  invoice_number: string
  invoice_date: string
  invoice_amount: string
  tax_amount: string
  currency: string
  buyer: string
  seller: string
  invoice_type: string
  note: string | null
  status: "draft" | "confirmed" | "voided"
  pdf_path: string
  pdf_original_name: string
  pdf_mime_type: string
  pdf_size: number
  deleted_at: string | null
  deleted_by_id: string | null
  created_at: string
  updated_at: string | null
  duplicate_warning?: string | null
  duplicate_invoice_owner_count?: number | null
}

export interface InvoiceFileCreate {
  invoice_number: string
  invoice_date: string
  invoice_amount: string
  tax_amount?: string
  currency: string
  buyer: string
  seller: string
  invoice_type: string
  note?: string | null
  pdf: File
}

export interface InvoiceFileUpdate {
  invoice_number?: string
  invoice_date?: string
  invoice_amount?: string
  tax_amount?: string
  currency?: string
  buyer?: string
  seller?: string
  invoice_type?: string
  note?: string | null
  pdf?: File
}

export interface InvoiceFileListResponse {
  data: InvoiceFile[]
  count: number
}

export interface ParsePreviewResponse {
  invoice_number: string | null
  invoice_date: string | null
  invoice_amount: string | null
  tax_amount: string | null
  currency: string | null
  buyer: string | null
  seller: string | null
  invoice_type: string | null
  note: string | null
}
