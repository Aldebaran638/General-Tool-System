export type MatchStatus = "confirmed" | "needs_review" | "cancelled" | "approved"

export type MatchLevel = "strong" | "weak" | "low"

export interface MatchSummary {
  total_confirmed: number
  total_approved: number
  total_cancelled: number
  total_needs_review: number
  total_unmatched_purchase_records: number
  total_available_invoices: number
}

export interface UnmatchedPurchaseRecord {
  id: string
  owner_id: string
  purchase_date: string
  amount: string
  currency: string
  order_name: string
  category: string
  subcategory: string | null
  note: string | null
  status: "submitted" | "approved"
}

export interface UnmatchedPurchaseRecordsResponse {
  count: number
  data: UnmatchedPurchaseRecord[]
}

export interface AvailableInvoice {
  id: string
  owner_id: string
  invoice_number: string
  invoice_date: string
  invoice_amount: string
  currency: string
  seller: string
  status: "confirmed"
}

export interface AvailableInvoicesResponse {
  count: number
  data: AvailableInvoice[]
}

export interface SearchableInvoice {
  id: string
  owner_id: string
  invoice_number: string
  invoice_date: string
  invoice_amount: string
  currency: string
  seller: string
  remaining_amount: string
  status: string
}

export interface SearchAvailableInvoicesResponse {
  count: number
  data: SearchableInvoice[]
}

export interface CandidateInvoice {
  invoice_file_id: string
  invoice_number: string
  invoice_date: string
  invoice_amount: string
  currency: string
  seller: string
  allocated_amount: string
  remaining_amount: string
  score: number
  score_breakdown: Record<string, number>
  level: MatchLevel
}

export interface CandidatesResponse {
  count: number
  data: CandidateInvoice[]
}

export interface InvoiceMatchPublic {
  id: string
  owner_id: string
  purchase_record_id: string
  invoice_file_id: string
  purchase_record_name: string | null
  purchase_date: string | null
  purchase_amount: string | null
  invoice_file_number: string | null
  invoice_date: string | null
  invoice_amount: string | null
  seller: string | null
  status: MatchStatus
  score: number
  score_breakdown: Record<string, number>
  review_reason: string | null
  confirmed_by_id: string | null
  confirmed_at: string | null
  cancelled_by_id: string | null
  cancelled_at: string | null
  approved_by_id: string | null
  approved_at: string | null
  created_at: string
  updated_at: string | null
}

export interface InvoiceMatchesPublic {
  count: number
  data: InvoiceMatchPublic[]
}

export interface ConfirmMatchRequest {
  purchase_record_id: string
  invoice_file_id: string
}
