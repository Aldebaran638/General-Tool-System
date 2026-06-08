import { Building2 } from "lucide-react"
import { registerTool } from "@/tools/registry"
import { WecomDepartmentSyncPage } from "./components/WecomDepartmentSyncPage"

registerTool({
  name: "wecom_department_sync",
  group: "data_sync",
  route: {
    path: "/wecom-department-sync",
    title: "企微部门同步 - 数据同步",
    component: WecomDepartmentSyncPage,
  },
  navigation: {
    title: "企微部门同步",
    icon: Building2,
    path: "/wecom-department-sync",
    requiresSuperuser: true,
  },
})

export { WecomDepartmentSyncPage }
