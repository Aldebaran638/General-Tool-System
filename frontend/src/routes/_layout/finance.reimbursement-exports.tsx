import { createFileRoute } from "@tanstack/react-router"

import { toolRegistry } from "@/tools/registry"

const tool = toolRegistry.getTool("reimbursement_exports")
const ReimbursementExportsPage = tool?.route.component

export const Route = createFileRoute("/_layout/finance/reimbursement-exports")({
  component: ReimbursementExportsRoute,
  head: () => ({
    meta: [
      {
        title: tool?.route.title || "报销导出",
      },
    ],
  }),
})

function ReimbursementExportsRoute() {
  if (!ReimbursementExportsPage) {
    return null
  }

  return <ReimbursementExportsPage />
}
