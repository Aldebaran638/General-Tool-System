import { createFileRoute } from "@tanstack/react-router"

import { toolRegistry } from "@/tools/registry"

const tool = toolRegistry.getTool("invoice_match_audit")
const InvoiceMatchAuditPage = tool?.route.component

export const Route = createFileRoute("/_layout/finance/invoice-match-audit")({
  component: InvoiceMatchAuditRoute,
  head: () => ({
    meta: [
      {
        title: tool?.route.title || "发票匹配审核",
      },
    ],
  }),
})

function InvoiceMatchAuditRoute() {
  if (!InvoiceMatchAuditPage) {
    return null
  }

  return <InvoiceMatchAuditPage />
}
