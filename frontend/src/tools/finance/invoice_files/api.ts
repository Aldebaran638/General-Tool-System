import { request as __request } from "@/client/core/request"
import { OpenAPI } from "@/client/core/OpenAPI"

import type {
  InvoiceFile,
  InvoiceFileCreate,
  InvoiceFileListResponse,
  InvoiceFileUpdate,
  ParsePreviewResponse,
} from "./types"

const BASE_URL = "/api/v1/finance/invoice-files"

export async function parsePreview(pdf: File): Promise<ParsePreviewResponse> {
  const formData = new FormData()
  formData.append("pdf", pdf)

  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/parse-preview`,
    body: formData,
    mediaType: "multipart/form-data",
  })

  return response as ParsePreviewResponse
}

export async function listInvoiceFiles(params?: {
  deleted?: boolean
  status?: string
  skip?: number
  limit?: number
}): Promise<InvoiceFileListResponse> {
  const response = await __request(OpenAPI, {
    method: "GET",
    url: BASE_URL,
    query: params,
  })

  return response as InvoiceFileListResponse
}

export async function getInvoiceFile(id: string): Promise<InvoiceFile> {
  const response = await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/${id}`,
  })

  return response as InvoiceFile
}

export async function createInvoiceFile(
  data: InvoiceFileCreate,
): Promise<InvoiceFile> {
  const formData = new FormData()
  formData.append("invoice_number", data.invoice_number)
  formData.append("invoice_date", data.invoice_date)
  formData.append("invoice_amount", data.invoice_amount)
  formData.append("tax_amount", data.tax_amount || "0.00")
  formData.append("currency", data.currency)
  formData.append("buyer", data.buyer)
  formData.append("seller", data.seller)
  formData.append("invoice_type", data.invoice_type)
  if (data.note !== undefined && data.note !== null) {
    formData.append("note", data.note)
  }
  formData.append("pdf", data.pdf)

  const response = await __request(OpenAPI, {
    method: "POST",
    url: BASE_URL,
    body: formData,
    mediaType: "multipart/form-data",
  })

  return response as InvoiceFile
}

export async function updateInvoiceFile(
  id: string,
  data: InvoiceFileUpdate,
): Promise<InvoiceFile> {
  const formData = new FormData()

  if (data.invoice_number !== undefined) {
    formData.append("invoice_number", data.invoice_number)
  }
  if (data.invoice_date !== undefined) {
    formData.append("invoice_date", data.invoice_date)
  }
  if (data.invoice_amount !== undefined) {
    formData.append("invoice_amount", data.invoice_amount)
  }
  if (data.tax_amount !== undefined) {
    formData.append("tax_amount", data.tax_amount)
  }
  if (data.currency !== undefined) {
    formData.append("currency", data.currency)
  }
  if (data.buyer !== undefined) {
    formData.append("buyer", data.buyer)
  }
  if (data.seller !== undefined) {
    formData.append("seller", data.seller)
  }
  if (data.invoice_type !== undefined) {
    formData.append("invoice_type", data.invoice_type)
  }
  if (data.note !== undefined) {
    formData.append("note", data.note || "")
  }
  if (data.pdf) {
    formData.append("pdf", data.pdf)
  }

  const response = await __request(OpenAPI, {
    method: "PATCH",
    url: `${BASE_URL}/${id}`,
    body: formData,
    mediaType: "multipart/form-data",
  })

  return response as InvoiceFile
}

export async function confirmInvoiceFile(id: string): Promise<InvoiceFile> {
  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/${id}/confirm`,
  })

  return response as InvoiceFile
}

export async function withdrawConfirmationInvoiceFile(
  id: string,
): Promise<InvoiceFile> {
  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/${id}/withdraw-confirmation`,
  })

  return response as InvoiceFile
}

export async function voidInvoiceFile(id: string): Promise<InvoiceFile> {
  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/${id}/void`,
  })

  return response as InvoiceFile
}

export async function restoreDraftInvoiceFile(
  id: string,
): Promise<InvoiceFile> {
  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/${id}/restore-draft`,
  })

  return response as InvoiceFile
}

export async function deleteInvoiceFile(id: string): Promise<void> {
  await __request(OpenAPI, {
    method: "DELETE",
    url: `${BASE_URL}/${id}`,
  })
}

export async function restoreInvoiceFile(id: string): Promise<InvoiceFile> {
  const response = await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/${id}/restore`,
  })

  return response as InvoiceFile
}

export async function downloadPdf(id: string): Promise<Blob> {
  const token = localStorage.getItem("access_token")
  const url = `${OpenAPI.BASE}${BASE_URL}/${id}/pdf`

  const response = await fetch(url, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  if (!response.ok) {
    throw new Error(`PDF 下载失败: ${response.status}`)
  }

  return response.blob()
}
