/**
 * Reimbursement Exports Tool Module
 *
 * Self-registers with the global tool registry on import.
 */

import { FileSpreadsheet } from "lucide-react"

import { registerTool } from "@/tools/registry"
import { ReimbursementExportsPage } from "./components/ReimbursementExportsPage"

registerTool({
  name: "reimbursement_exports",
  group: "finance",
  route: {
    path: "/finance/reimbursement-exports",
    title: "报销导出 - 发票管理系统",
    titleKey: "finance.reimbursementExports.title",
    component: ReimbursementExportsPage,
  },
  navigation: {
    title: "报销导出",
    titleKey: "finance.reimbursementExports.title",
    icon: FileSpreadsheet,
    path: "/finance/reimbursement-exports",
    requiresSuperuser: true,
  },
})

export { ReimbursementExportsPage }
export * from "./api"
export * from "./types"
export * from "./schemas"
