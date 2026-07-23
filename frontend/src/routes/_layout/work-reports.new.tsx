import { createFileRoute } from "@tanstack/react-router"

import WorkReportForm from "@/tools/work-report/WorkReportForm"

export const Route = createFileRoute("/_layout/work-reports/new")({
  component: WorkReportForm,
  head: () => ({ meta: [{ title: "填写工作汇报 - 项目管理面板" }] }),
})
