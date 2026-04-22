/**
 * Project Management Tool Module
 *
 * Self-registers with the global tool registry on import.
 */

import { Briefcase } from "lucide-react"

import { registerTool } from "@/tools/registry"
import { ProjectManagementPage } from "./components/ProjectManagementPage"

registerTool({
  name: "project_management",
  group: "workbench",
  route: {
    path: "/items",
    title: "Items - FastAPI Cloud",
    component: ProjectManagementPage,
  },
  navigation: {
    title: "项目管理",
    icon: Briefcase,
    path: "/items",
    requiresSuperuser: false,
  },
})

// Re-exports for direct usage
export { ProjectManagementPage }
export * from "./api"
export * from "./types"
export * from "./schemas"
