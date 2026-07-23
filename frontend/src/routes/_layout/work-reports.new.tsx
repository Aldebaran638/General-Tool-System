import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"

import WorkReportForm from "@/tools/work-report/WorkReportForm"

const searchSchema = z.object({
  reportType: z.enum(["weekly", "monthly"]).optional().catch(undefined),
  periodKey: z.string().optional().catch(undefined),
})

export const Route = createFileRoute("/_layout/work-reports/new")({
  component: WorkReportFormPage,
  validateSearch: searchSchema,
  head: () => ({ meta: [{ title: "填写工作汇报 - 项目管理面板" }] }),
})

function WorkReportFormPage() {
  const search = Route.useSearch()
  return (
    <WorkReportForm
      initialReportType={search.reportType}
      initialPeriodKey={search.periodKey}
    />
  )
}
