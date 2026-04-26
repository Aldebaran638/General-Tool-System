import { request as __request } from "@/client/core/request"
import { OpenAPI } from "@/client/core/OpenAPI"

import type {
  GenerateRequest,
  PurgeResult,
  RecordsPublic,
  RecordsQuery,
  ReimbursementExportDetailPublic,
  ReimbursementExportPublic,
  ReimbursementExportsPublic,
  SettingsResponse,
  SettingsUpdate,
} from "./types"

const BASE_URL = "/api/v1/finance/reimbursement-exports"

export async function listRecords(
  params?: RecordsQuery,
): Promise<RecordsPublic> {
  const response = await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/records`,
    query: params,
  })
  return response as RecordsPublic
}

export async function generateExport(
  data: GenerateRequest,
): Promise<ReimbursementExportPublic> {
  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/generate`,
    body: data,
    mediaType: "application/json",
  })
  return response as ReimbursementExportPublic
}

export async function listHistory(params?: {
  skip?: number
  limit?: number
  created_at_from?: string
  created_at_to?: string
  created_by_id?: string
  currency?: string
}): Promise<ReimbursementExportsPublic> {
  const response = await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/history`,
    query: params,
  })
  return response as ReimbursementExportsPublic
}

export async function getExport(
  exportId: string,
): Promise<ReimbursementExportDetailPublic> {
  const response = await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/${exportId}`,
  })
  return response as ReimbursementExportDetailPublic
}

export async function getSettings(): Promise<SettingsResponse> {
  const response = await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/settings`,
  })
  return response as SettingsResponse
}

export async function updateSettings(
  data: SettingsUpdate,
): Promise<SettingsResponse> {
  const response = await __request(OpenAPI, {
    method: "PUT",
    url: `${BASE_URL}/settings`,
    body: data,
    mediaType: "application/json",
  })
  return response as SettingsResponse
}

export async function purgeExpiredFiles(): Promise<PurgeResult> {
  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/purge-expired-files`,
  })
  return response as PurgeResult
}

/**
 * Download exported Excel via fetch + Authorization Bearer header.
 * Triggers browser download with the suggested filename.
 *
 * Throws an Error whose .message is one of:
 *   - "expired" when server returns 410 Gone
 *   - "not_found" when 404
 *   - "forbidden" when 403
 *   - "unauthorized" when 401
 *   - generic message otherwise
 */
export async function downloadExport(
  exportId: string,
  fallbackFilename: string,
): Promise<void> {
  const tokenResolver = OpenAPI.TOKEN
  let token = ""
  if (typeof tokenResolver === "function") {
    const resolved = await tokenResolver({} as never)
    token = resolved ?? ""
  } else if (typeof tokenResolver === "string") {
    token = tokenResolver
  }

  const url = `${OpenAPI.BASE}${BASE_URL}/${exportId}/download`
  const response = await fetch(url, {
    method: "GET",
    headers: {
      Authorization: token ? `Bearer ${token}` : "",
    },
  })

  if (!response.ok) {
    if (response.status === 410) throw new Error("expired")
    if (response.status === 404) throw new Error("not_found")
    if (response.status === 403) throw new Error("forbidden")
    if (response.status === 401) throw new Error("unauthorized")
    throw new Error(`download_failed_${response.status}`)
  }

  const blob = await response.blob()
  const disposition = response.headers.get("content-disposition") || ""
  const match = disposition.match(/filename\*?=(?:UTF-8''|")?([^;"']+)/i)
  const filename = match ? decodeURIComponent(match[1]) : fallbackFilename

  const objectUrl = window.URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = objectUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(objectUrl)
}
