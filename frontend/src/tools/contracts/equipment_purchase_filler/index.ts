/**
 * Equipment Purchase Contract Filler Tool Module
 *
 * Self-registers with the global tool registry on import.
 */

import { FileSignature } from "lucide-react"

import { registerTool } from "@/tools/registry"
import { EquipmentPurchaseFillerPage } from "./components/EquipmentPurchaseFillerPage"

registerTool({
  name: "equipment_purchase_filler",
  group: "contracts",
  route: {
    path: "/contracts/equipment-purchase-filler",
    title: "合同填充 - 设备购销合同",
    component: EquipmentPurchaseFillerPage,
  },
  navigation: {
    title: "设备购销合同填充",
    titleKey: "contracts.equipmentPurchase.title",
    icon: FileSignature,
    path: "/contracts/equipment-purchase-filler",
    requiresSuperuser: false,
  },
})

export { EquipmentPurchaseFillerPage }
export * from "./api"
export * from "./types"
export * from "./schemas"
