/**
 * Invoice Matching Tool Module
 *
 * Self-registers with the global tool registry on import.
 */

import { Link2 } from "lucide-react"

import { registerTool } from "@/tools/registry"

import { InvoiceMatchingPage } from "./components/InvoiceMatchingPage"

registerTool({
  name: "invoice_matching",
  group: "finance",
  route: {
    path: "/finance/invoice-matching",
    title: "发票匹配 - 发票管理系统",
    titleKey: "finance.invoiceMatching.title",
    component: InvoiceMatchingPage,
  },
  navigation: {
    title: "发票匹配",
    titleKey: "finance.invoiceMatching.title",
    icon: Link2,
    path: "/finance/invoice-matching",
    requiresSuperuser: false,
  },
})

export { InvoiceMatchingPage }
export * from "./api"
export * from "./types"
