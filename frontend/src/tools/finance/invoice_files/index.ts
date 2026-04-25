/**
 * Invoice Files Tool Module
 *
 * Self-registers with the global tool registry on import.
 */

import { FileText } from "lucide-react"

import { registerTool } from "@/tools/registry"
import { InvoiceFilesPage } from "./components/InvoiceFilesPage"

registerTool({
  name: "invoice_files",
  group: "finance",
  route: {
    path: "/finance/invoice-files",
    title: "发票文件 - 通用工具系统",
    component: InvoiceFilesPage,
  },
  navigation: {
    title: "发票文件",
    icon: FileText,
    path: "/finance/invoice-files",
    requiresSuperuser: false,
  },
})

export { InvoiceFilesPage }
export * from "./api"
export * from "./types"
export * from "./schemas"
