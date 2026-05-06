/**
 * Invoice Match Audit Tool Module
 *
 * Self-registers with the global tool registry on import.
 * Admin-only tool for auditing invoice matches across all users.
 */

import { ClipboardCheck } from "lucide-react"

import { registerTool } from "@/tools/registry"

import { InvoiceMatchAuditPage } from "./components/InvoiceMatchAuditPage"

registerTool({
  name: "invoice_match_audit",
  group: "finance",
  route: {
    path: "/finance/invoice-match-audit",
    title: "发票匹配审核 - 发票管理系统",
    titleKey: "finance.invoiceMatchAudit.title",
    component: InvoiceMatchAuditPage,
  },
  navigation: {
    title: "发票匹配审核",
    titleKey: "finance.invoiceMatchAudit.title",
    icon: ClipboardCheck,
    path: "/finance/invoice-match-audit",
    requiresSuperuser: true,
  },
})

export { InvoiceMatchAuditPage }
