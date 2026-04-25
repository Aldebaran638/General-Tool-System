import { createFileRoute } from "@tanstack/react-router"

import { toolRegistry } from "@/tools/registry"

const tool = toolRegistry.getTool("invoice_files")
const InvoiceFilesPage = tool?.route.component

export const Route = createFileRoute("/_layout/finance/invoice-files")({
  component: InvoiceFilesRoute,
  head: () => ({
    meta: [
      {
        title: tool?.route.title || "发票文件",
      },
    ],
  }),
})

function InvoiceFilesRoute() {
  if (!InvoiceFilesPage) {
    return null
  }

  return <InvoiceFilesPage />
}
