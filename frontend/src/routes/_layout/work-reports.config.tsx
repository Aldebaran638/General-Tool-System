import { createFileRoute } from "@tanstack/react-router"

import WorkReportFieldConfig from "@/tools/work-report/WorkReportFieldConfig"

export const Route = createFileRoute("/_layout/work-reports/config")({
  component: WorkReportFieldConfig,
  head: () => ({ meta: [{ title: "工作汇报字段配置 - 项目管理面板" }] }),
})
