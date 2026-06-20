export interface ContractField {
  key: string
  label: string
  type: string
  default_value: string | null
  required: boolean
}

export interface PreviewSegment {
  type: "paragraph" | "table"
  text?: string
  style?: string
  rows?: string[][]
}

export interface EquipmentItem {
  name: string
  brand: string
  spec: string
  unit: string
  quantity: string
  unit_price: string
  total_price: string
}

export interface FilledVersion {
  id: string
  created_by_id: string
  version_name: string
  description: string | null
  field_values: Record<string, string>
  equipment_items: EquipmentItem[] | null
  output_filename: string | null
  output_file_path: string | null
  output_file_size: number | null
  created_at: string
  updated_at: string | null
}

export interface FilledVersionCreate {
  version_name: string
  description?: string | null
  field_values: Record<string, string>
  equipment_items?: EquipmentItem[] | null
}

export interface FilledVersionUpdate {
  version_name?: string
  description?: string | null
  field_values?: Record<string, string>
  equipment_items?: EquipmentItem[] | null
}

export interface ExportRequest {
  filename?: string | null
}

export interface ExportResponse {
  download_url: string
  filename: string
}
