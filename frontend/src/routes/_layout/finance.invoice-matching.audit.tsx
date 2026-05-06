import { createFileRoute } from "@tanstack/react-router"

import { AuditPage } from "@/tools/finance/invoice_matching/components/AuditPage"

export const Route = createFileRoute("/_layout/finance/invoice-matching/audit")({
  component: AuditRoute,
  head: () => ({
    meta: [
      {
        title: "发票匹配审核 - 发票管理系统",
      },
    ],
  }),
})

function AuditRoute() {
  return <AuditPage />
}
