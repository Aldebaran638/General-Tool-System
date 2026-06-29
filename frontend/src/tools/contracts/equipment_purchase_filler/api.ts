import { request as __request } from "@/client/core/request"
import { OpenAPI } from "@/client/core/OpenAPI"

import type {
  ContractField,
  EquipmentItem,
  ExportRequest,
  ExportResponse,
  FilledVersion,
  FilledVersionCreate,
  FilledVersionUpdate,
  PreviewSegment,
} from "./types"

const BASE_URL = "/api/v1/contracts/equipment-purchase-filler"

export async function listFields(): Promise<ContractField[]> {
  const response = (await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/fields`,
  })) as { data: ContractField[] }
  return response.data
}

export async function getPreview(): Promise<PreviewSegment[]> {
  const response = (await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/preview`,
  })) as { data: PreviewSegment[] }
  return response.data
}

export async function listVersions(): Promise<FilledVersion[]> {
  const response = (await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/versions`,
  })) as { data: FilledVersion[]; count: number }
  return response.data
}

export async function getVersion(id: string): Promise<FilledVersion> {
  return (await __request(OpenAPI, {
    method: "GET",
    url: `${BASE_URL}/versions/${id}`,
  })) as FilledVersion
}

export async function createVersion(data: FilledVersionCreate): Promise<FilledVersion> {
  return (await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/versions`,
    body: data,
  })) as FilledVersion
}

export async function updateVersion(
  id: string,
  data: FilledVersionUpdate,
): Promise<FilledVersion> {
  return (await __request(OpenAPI, {
    method: "PATCH",
    url: `${BASE_URL}/versions/${id}`,
    body: data,
  })) as FilledVersion
}

export async function deleteVersion(id: string): Promise<void> {
  await __request(OpenAPI, {
    method: "DELETE",
    url: `${BASE_URL}/versions/${id}`,
  })
}

export async function exportVersion(
  id: string,
  request: ExportRequest = {},
): Promise<ExportResponse> {
  return (await __request(OpenAPI, {
    method: "POST",
    url: `${BASE_URL}/versions/${id}/export`,
    body: request,
  })) as ExportResponse
}

export async function downloadContractDocx(url: string): Promise<Blob> {
  const token = localStorage.getItem("access_token")
  const fullUrl = url.startsWith("http") ? url : `${OpenAPI.BASE}${url}`

  const response = await fetch(fullUrl, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  if (!response.ok) {
    throw new Error(`合同下载失败: ${response.status}`)
  }

  return response.blob()
}

export const EQUIPMENT_TABLE_COLUMNS = [
  { key: "name", label: "设备名称" },
  { key: "brand", label: "品牌" },
  { key: "spec", label: "规格" },
  { key: "unit", label: "单位" },
  { key: "quantity", label: "数量" },
  { key: "unit_price", label: "单价（RMB）" },
  { key: "total_price", label: "总价（RMB）" },
]

export function createEmptyEquipmentItem(): EquipmentItem {
  return {
    name: "",
    brand: "",
    spec: "",
    unit: "",
    quantity: "",
    unit_price: "",
    total_price: "",
  }
}
