import { createFileRoute } from "@tanstack/react-router"

import { toolRegistry } from "@/tools/registry"

const tool = toolRegistry.getTool("purchase_records")
const PurchaseRecordsPage = tool?.route.component

export const Route = createFileRoute("/_layout/finance/purchase-records")({
  component: PurchaseRecordsRoute,
  head: () => ({
    meta: [
      {
        title: tool?.route.title || "购买记录",
      },
    ],
  }),
})

function PurchaseRecordsRoute() {
  if (!PurchaseRecordsPage) {
    return null
  }

  return <PurchaseRecordsPage />
}
