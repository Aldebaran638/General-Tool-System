import { createFileRoute } from "@tanstack/react-router"

import WorkReportHistory from "@/tools/work-report/WorkReportHistory"

export const Route = createFileRoute("/_layout/work-reports/mine")({
  component: () => <WorkReportHistory mode="mine" />,
  head: () => ({ meta: [{ title: "我的汇报 - 项目管理面板" }] }),
})
