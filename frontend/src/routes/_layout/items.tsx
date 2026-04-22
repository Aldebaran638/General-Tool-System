import { createFileRoute } from "@tanstack/react-router"

import { toolRegistry } from "@/tools/registry"

// Legacy route file - thin wrapper around registry
// The actual component comes from the tool module registered in the registry
const tool = toolRegistry.getTool("project_management")
const ProjectManagementPage = tool?.route.component

export const Route = createFileRoute("/_layout/items")({
  component: ProjectManagementPage || (() => null),
  head: () => ({
    meta: [
      {
        title: tool?.route.title || "Items",
      },
    ],
  }),
})
