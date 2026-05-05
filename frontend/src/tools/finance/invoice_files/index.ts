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
    title: "发票文件 - 发票管理系统",
    component: InvoiceFilesPage,
  },
  navigation: {
    title: "发票文件",
    titleKey: "finance.invoiceFiles.title",
    icon: FileText,
    path: "/finance/invoice-files",
    requiresSuperuser: false,
  },
})

export { InvoiceFilesPage }
export * from "./api"
export * from "./types"
export * from "./schemas"
