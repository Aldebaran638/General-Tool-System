import { Users } from "lucide-react"
import { registerTool } from "@/tools/registry"
import { WecomMemberSyncPage } from "./components/WecomMemberSyncPage"

registerTool({
  name: "wecom_member_sync",
  group: "data_sync",
  route: {
    path: "/wecom-member-sync",
    title: "企微成员同步 - 数据同步",
    component: WecomMemberSyncPage,
  },
  navigation: {
    title: "企微成员同步",
    icon: Users,
    path: "/wecom-member-sync",
    requiresSuperuser: true,
  },
})

export { WecomMemberSyncPage }
