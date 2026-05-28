import {
  getDepartmentStatus,
  getDepartmentTasks,
  getDepartments,
  triggerDepartmentSync,
} from "@/tools/data_sync/_shared/api"
import { SyncPage } from "@/tools/data_sync/_shared/SyncPage"

export function WecomDepartmentSyncPage() {
  return (
    <SyncPage
      title="企微部门同步"
      description="将企业微信通讯录中的部门树同步到本地数据库，用于考试/培训的组织架构选择。"
      statusQueryKey={["sync-status", "wecom_department"]}
      tasksQueryKey={(page) => ["sync-tasks", "wecom_department", page]}
      fetchStatus={getDepartmentStatus}
      fetchTasks={(page) => getDepartmentTasks(page)}
      triggerSync={(mode) => triggerDepartmentSync({ mode })}
      fetchDepartments={(page) => getDepartments(page)}
    />
  )
}
