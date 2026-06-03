import { createFileRoute, redirect } from "@tanstack/react-router"

import { UsersService } from "@/client"
import { SystemDashboardPage } from "@/tools/workbench/system_dashboard/components/SystemDashboardPage"

export const Route = createFileRoute("/_layout/system-dashboard")({
  component: SystemDashboardPage,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (!user.is_superuser) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "系统总览 - 考试管理系统" }],
  }),
})
