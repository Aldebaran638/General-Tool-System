/**
 * System Dashboard Tool Module
 *
 * Displays aggregate system-level statistics for admins:
 * exam count, participation, pass rate, question/paper counts,
 * and question type distribution.
 *
 * Self-registers with the global tool registry on import.
 */

import { BarChart3 } from "lucide-react"

import { registerTool } from "@/tools/registry"
import { SystemDashboardPage } from "./components/SystemDashboardPage"

registerTool({
  name: "system_dashboard",
  group: "workbench",
  route: {
    path: "/system-dashboard",
    title: "系统总览 - 考试管理系统",
    component: SystemDashboardPage,
  },
  navigation: {
    title: "系统总览",
    icon: BarChart3,
    path: "/system-dashboard",
    requiresSuperuser: true,
  },
})

export { SystemDashboardPage }
export * from "./api"
export * from "./types"
