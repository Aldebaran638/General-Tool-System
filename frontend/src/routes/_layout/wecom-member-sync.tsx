import { createFileRoute } from "@tanstack/react-router"
import { toolRegistry } from "@/tools/registry"
import { WecomMemberSyncPage } from "@/tools/data_sync/wecom_member_sync/components/WecomMemberSyncPage"

const tool = toolRegistry.getTool("wecom_member_sync")

export const Route = createFileRoute("/_layout/wecom-member-sync")({
  component: WecomMemberSyncPage,
  head: () => ({
    meta: [{ title: tool?.route.title || "企微成员同步" }],
  }),
})
