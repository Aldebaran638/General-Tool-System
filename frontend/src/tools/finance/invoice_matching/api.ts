import { request as __request } from "@/client/core/request"
import { OpenAPI } from "@/client/core/OpenAPI"

import type {
  AvailableInvoicesResponse,
  CandidatesResponse,
  ConfirmMatchRequest,
  InvoiceMatchPublic,
  InvoiceMatchesPublic,
  MatchStatus,
  MatchSummary,
  SearchAvailableInvoicesResponse,
  UnmatchedPurchaseRecordsResponse,
} from "./types"

const BASE_URL = "/api/v1/finance/invoice-matching"

export async function getMatchSummary(): Promise<MatchSummary> {
  const response = await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/summary`,
  })
  return response as MatchSummary
}

export async function listUnmatchedPurchaseRecords(params?: {
  skip?: number
  limit?: number
}): Promise<UnmatchedPurchaseRecordsResponse> {
  const response = await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/unmatched-purchase-records`,
    query: params,
  })
  return response as UnmatchedPurchaseRecordsResponse
}

export async function listAvailableInvoices(params?: {
  skip?: number
  limit?: number
}): Promise<AvailableInvoicesResponse> {
  const response = await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/available-invoices`,
    query: params,
  })
  return response as AvailableInvoicesResponse
}

export async function searchAvailableInvoices(params: {
  purchase_record_id: string
  search?: string
}): Promise<SearchAvailableInvoicesResponse> {
  const response = await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/available-invoices/search`,
    query: params,
  })
  return response as SearchAvailableInvoicesResponse
}

export async function listCandidates(
  purchaseRecordId: string,
): Promise<CandidatesResponse> {
  const response = await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/candidates`,
    query: { purchase_record_id: purchaseRecordId },
  })
  return response as CandidatesResponse
}

export async function listMatches(params?: {
  status?: MatchStatus
  skip?: number
  limit?: number
}): Promise<InvoiceMatchesPublic> {
  const response = await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/matches`,
    query: params,
  })
  return response as InvoiceMatchesPublic
}

export async function confirmMatch(
  data: ConfirmMatchRequest,
): Promise<InvoiceMatchPublic> {
  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/confirm`,
    body: data,
    mediaType: "application/json",
  })
  return response as InvoiceMatchPublic
}

export async function cancelMatch(matchId: string): Promise<InvoiceMatchPublic> {
  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/${matchId}/cancel`,
  })
  return response as InvoiceMatchPublic
}

export async function reconfirmMatch(
  matchId: string,
): Promise<InvoiceMatchPublic> {
  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/${matchId}/reconfirm`,
  })
  return response as InvoiceMatchPublic
}
