import {
  getMemberStatus,
  getMemberTasks,
  getMembers,
  triggerMemberSync,
} from "@/tools/data_sync/_shared/api"
import { SyncPage } from "@/tools/data_sync/_shared/SyncPage"

export function WecomMemberSyncPage() {
  return (
    <SyncPage
      title="企微成员同步"
      description="将企业微信通讯录中的成员同步到本地数据库，包含离职软删除处理。"
      statusQueryKey={["sync-status", "wecom_member"]}
      tasksQueryKey={(page) => ["sync-tasks", "wecom_member", String(page)]}
      fetchStatus={getMemberStatus}
      fetchTasks={(page) => getMemberTasks(page)}
      triggerSync={(mode) => triggerMemberSync({ mode })}
      fetchMembers={(page, q) => getMembers(page, 20, q)}
    />
  )
}
