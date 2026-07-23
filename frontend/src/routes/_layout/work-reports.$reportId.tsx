import { createFileRoute } from "@tanstack/react-router"

import WorkReportDetailView from "@/tools/work-report/WorkReportDetailView"

export const Route = createFileRoute("/_layout/work-reports/$reportId")({
  component: ReportDetailPage,
  head: () => ({ meta: [{ title: "汇报详情 - 项目管理面板" }] }),
})

function ReportDetailPage() {
  const { reportId } = Route.useParams()
  return <WorkReportDetailView reportId={reportId} />
}
