import { createFileRoute } from "@tanstack/react-router"
import { ProjectManagementPage } from "@/tools/workbench/project_management/components/ProjectManagementPage"

export const Route = createFileRoute("/_layout/items")({
  component: ProjectManagementPage,
  head: () => ({
    meta: [
      {
        title: "Items - FastAPI Cloud",
      },
    ],
  }),
})
