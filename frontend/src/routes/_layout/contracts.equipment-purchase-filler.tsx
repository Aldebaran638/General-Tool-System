import { createFileRoute } from "@tanstack/react-router"

import { toolRegistry } from "@/tools/registry"

const tool = toolRegistry.getTool("equipment_purchase_filler")
const EquipmentPurchaseFillerPage = tool?.route.component

export const Route = createFileRoute("/_layout/contracts/equipment-purchase-filler")({
  component: EquipmentPurchaseFillerRoute,
  head: () => ({
    meta: [
      {
        title: tool?.route.title || "设备购销合同填充",
      },
    ],
  }),
})

function EquipmentPurchaseFillerRoute() {
  if (!EquipmentPurchaseFillerPage) {
    return null
  }

  return <EquipmentPurchaseFillerPage />
}
