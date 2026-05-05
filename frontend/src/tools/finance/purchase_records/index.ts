/**
 * Purchase Records Tool Module
 *
 * Self-registers with the global tool registry on import.
 */

import { Receipt } from "lucide-react"

import { registerTool } from "@/tools/registry"
import { PurchaseRecordsPage } from "./components/PurchaseRecordsPage"

registerTool({
  name: "purchase_records",
  group: "finance",
  route: {
    path: "/finance/purchase-records",
    title: "购买记录 - 发票管理系统",
    component: PurchaseRecordsPage,
  },
  navigation: {
    title: "购买记录",
    titleKey: "finance.purchaseRecords.title",
    icon: Receipt,
    path: "/finance/purchase-records",
    requiresSuperuser: false,
  },
})

export { PurchaseRecordsPage }
export * from "./api"
export * from "./types"
export * from "./schemas"
