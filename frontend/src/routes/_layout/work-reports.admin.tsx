import { createFileRoute } from "@tanstack/react-router"

import WorkReportHistory from "@/tools/work-report/WorkReportHistory"

export const Route = createFileRoute("/_layout/work-reports/admin")({
  component: () => <WorkReportHistory mode="admin" />,
  head: () => ({ meta: [{ title: "全部汇报 - 项目管理面板" }] }),
})
