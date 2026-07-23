import { createFileRoute } from "@tanstack/react-router"

import WorkReportReminders from "@/tools/work-report/WorkReportReminders"

export const Route = createFileRoute("/_layout/work-reports/reminders")({
  component: WorkReportReminders,
  head: () => ({ meta: [{ title: "工作汇报提醒 - 项目管理面板" }] }),
})
