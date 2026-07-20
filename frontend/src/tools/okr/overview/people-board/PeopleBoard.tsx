import { useState } from "react"
import { useTranslation } from "react-i18next"
import type { UserStats } from "@/client"
import { cn } from "@/lib/utils"
import { UserRow, userRowGridColumns } from "./UserRow"

interface PeopleBoardProps {
  users: UserStats[]
}

/**
 * Member list of the people board. Any number of rows may be expanded at
 * the same time; the expanded state is kept locally keyed by user id.
 */
export function PeopleBoard({ users }: PeopleBoardProps) {
  const { t } = useTranslation()
  const [openIds, setOpenIds] = useState<Record<string, boolean>>({})

  const toggle = (id: string) => {
    setOpenIds((current) => ({ ...current, [id]: !current[id] }))
  }

  if (users.length === 0) {
    return (
      <p className="text-body text-muted-foreground">
        {t("okr.noMembers", "暂无成员数据")}
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div
        className={cn(
          "grid items-center gap-3 px-4 text-caption text-muted-foreground",
          userRowGridColumns,
        )}
      >
        <span>{t("okr.memberName", "姓名")}</span>
        <span>{t("okr.krTable.department", "部门")}</span>
        <span>{t("okr.krCount", "KR 数量")}</span>
        <span>{t("okr.avgProgress", "平均进度")}</span>
        <span className="size-4" />
      </div>
      {users.map((stats) => (
        <UserRow
          key={stats.user.id}
          stats={stats}
          open={Boolean(openIds[stats.user.id])}
          onToggle={() => toggle(stats.user.id)}
        />
      ))}
    </div>
  )
}
