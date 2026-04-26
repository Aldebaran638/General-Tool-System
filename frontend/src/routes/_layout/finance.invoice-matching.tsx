import { createFileRoute } from "@tanstack/react-router"

import { toolRegistry } from "@/tools/registry"

const tool = toolRegistry.getTool("invoice_matching")
const InvoiceMatchingPage = tool?.route.component

export const Route = createFileRoute("/_layout/finance/invoice-matching")({
  component: InvoiceMatchingRoute,
  head: () => ({
    meta: [
      {
        title: tool?.route.title || "发票匹配",
      },
    ],
  }),
})

function InvoiceMatchingRoute() {
  if (!InvoiceMatchingPage) {
    return null
  }

  return <InvoiceMatchingPage />
}
