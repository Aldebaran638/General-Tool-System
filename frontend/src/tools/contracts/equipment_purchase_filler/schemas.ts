import { z } from "zod"

export interface EquipmentPurchaseFillerFormValues {
  version_name: string
  description?: string
  field_values: Record<string, string>
  equipment_items?: import("./types").EquipmentItem[]
}

export function createEquipmentPurchaseFillerSchemas(t: (key: string) => string) {
  const versionNameSchema = z
    .string()
    .min(1, { message: t("contracts.equipmentPurchase.validation.versionNameRequired") })

  return { versionNameSchema }
}
