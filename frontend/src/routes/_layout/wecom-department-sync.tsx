import { createFileRoute } from "@tanstack/react-router"
import { toolRegistry } from "@/tools/registry"
import { WecomDepartmentSyncPage } from "@/tools/data_sync/wecom_department_sync/components/WecomDepartmentSyncPage"

const tool = toolRegistry.getTool("wecom_department_sync")

export const Route = createFileRoute("/_layout/wecom-department-sync")({
  component: WecomDepartmentSyncPage,
  head: () => ({
    meta: [{ title: tool?.route.title || "企微部门同步" }],
  }),
})
