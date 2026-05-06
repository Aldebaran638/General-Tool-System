import { request as __request } from "@/client/core/request"
import { OpenAPI } from "@/client/core/OpenAPI"

import type {
  PurchaseRecord,
  PurchaseRecordCreate,
  PurchaseRecordListResponse,
  PurchaseRecordUpdate,
  OcrPreviewResponse,
} from "./types"

const BASE_URL = "/api/v1/finance/purchase-records"

export async function ocrPreview(screenshot: File): Promise<OcrPreviewResponse> {
  const formData = new FormData()
  formData.append("screenshot", screenshot)

  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/ocr-preview`,
    body: formData,
    mediaType: "multipart/form-data",
  })

  return response as OcrPreviewResponse
}

export async function listPurchaseRecords(params?: {
  deleted?: boolean
  skip?: number
  limit?: number
}): Promise<PurchaseRecordListResponse> {
  const response = await __request(OpenAPI, {
    method: "GET",
    url: BASE_URL,
    query: params,
  })

  return response as PurchaseRecordListResponse
}

export async function getPurchaseRecord(id: string): Promise<PurchaseRecord> {
  const response = await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/${id}`,
  })

  return response as PurchaseRecord
}

export async function createPurchaseRecord(
  data: PurchaseRecordCreate,
): Promise<PurchaseRecord> {
  const formData = new FormData()
  formData.append("purchase_date", data.purchase_date)
  formData.append("amount", data.amount)
  formData.append("currency", data.currency)
  formData.append("order_name", data.order_name)
  formData.append("category", data.category)
  if (data.subcategory) {
    formData.append("subcategory", data.subcategory)
  }
  if (data.note) {
    formData.append("note", data.note)
  }
  formData.append("screenshot", data.screenshot)

  const response = await __request(OpenAPI, {
    method: "POST",
    url: BASE_URL,
    body: formData,
    mediaType: "multipart/form-data",
  })

  return response as PurchaseRecord
}

export async function updatePurchaseRecord(
  id: string,
  data: PurchaseRecordUpdate,
): Promise<PurchaseRecord> {
  const formData = new FormData()

  if (data.purchase_date) {
    formData.append("purchase_date", data.purchase_date)
  }
  if (data.amount) {
    formData.append("amount", data.amount)
  }
  if (data.currency) {
    formData.append("currency", data.currency)
  }
  if (data.order_name) {
    formData.append("order_name", data.order_name)
  }
  if (data.category) {
    formData.append("category", data.category)
  }
  if (data.subcategory !== undefined) {
    if (data.subcategory === null) {
      formData.append("subcategory", "")
    } else {
      formData.append("subcategory", data.subcategory)
    }
  }
  if (data.note !== undefined) {
    formData.append("note", data.note || "")
  }
  if (data.screenshot) {
    formData.append("screenshot", data.screenshot)
  }

  const response = await __request(OpenAPI, {
    method: "PATCH",
    url: `${BASE_URL}/${id}`,
    body: formData,
    mediaType: "multipart/form-data",
  })

  return response as PurchaseRecord
}

export async function submitPurchaseRecord(id: string): Promise<PurchaseRecord> {
  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/${id}/submit`,
  })

  return response as PurchaseRecord
}

export async function withdrawPurchaseRecord(id: string): Promise<PurchaseRecord> {
  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/${id}/withdraw`,
  })

  return response as PurchaseRecord
}

export async function deletePurchaseRecord(id: string): Promise<void> {
  await __request(OpenAPI, {
    method: "DELETE",
    url: `${BASE_URL}/${id}`,
  })
}

export async function restorePurchaseRecord(id: string): Promise<PurchaseRecord> {
  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/${id}/restore`,
  })

  return response as PurchaseRecord
}

export async function downloadScreenshot(id: string): Promise<Blob> {
  const token = localStorage.getItem("access_token")
  const url = `${OpenAPI.BASE}/api/v1/files/screenshots/${id}`

  const response = await fetch(url, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  if (!response.ok) {
    throw new Error(`截图下载失败: ${response.status}`)
  }

  return response.blob()
}

export function getScreenshotUrl(id: string): string {
  return `${OpenAPI.BASE}${BASE_URL}/${id}/screenshot`
}
