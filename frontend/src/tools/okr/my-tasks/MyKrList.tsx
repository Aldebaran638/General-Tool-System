import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"

import type { KeyResultPublic } from "@/client"
import { OkrService } from "@/client"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import ProgressEditor from "@/tools/okr/my-tasks/ProgressEditor"

export type MyKrFilter = "all" | "active" | "done" | "due_soon" | "overdue"

interface MyKrListProps {
  filter: MyKrFilter
}

const MyKrList = ({ filter }: MyKrListProps) => {
  const { t } = useTranslation()

  const { data, isPending } = useQuery({
    queryKey: ["my-krs", filter],
    queryFn: () => OkrService.readMyKrs({ filter }),
    // 切换筛选时保留上一份数据，避免列表闪烁
    placeholderData: (previousData) => previousData,
  })

  if (isPending) {
    return (
      <div className="flex flex-col gap-4">
        {Array.from({ length: 3 }).map((_, index) => (
          <Skeleton key={index} className="h-28 w-full rounded-lg" />
        ))}
      </div>
    )
  }

  const krs = data?.data ?? []

  if (krs.length === 0) {
    return (
      <p className="py-12 text-center text-body text-muted-foreground">
        {t("okr.my.empty", "当前筛选下没有任务。")}
      </p>
    )
  }

  const today = new Date().toISOString().slice(0, 10)

  return (
    <div className="flex flex-col gap-4">
      {krs.map((kr: KeyResultPublic) => {
        const progress = Math.round(kr.progress ?? 0)
        const deadline = kr.deadline.slice(0, 10)
        const isOverdue = deadline < today && progress < 100

        return (
          <div
            key={kr.id}
            className="rounded-lg border border-border bg-card p-4 text-card-foreground shadow-sm"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <h3 className="text-subheading">{kr.title}</h3>
                {kr.description && (
                  <p className="mt-1 line-clamp-2 text-body text-muted-foreground">
                    {kr.description}
                  </p>
                )}
              </div>
              <ProgressEditor kr={kr} />
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-1 text-caption text-muted-foreground">
              <span>
                {t("okr.my.department", "部门")}: {kr.department?.name ?? "—"}
              </span>
              <span>
                {t("okr.my.startDate", "开始时间")}:{" "}
                {kr.start_date.slice(0, 10)}
              </span>
              <span className={cn(isOverdue && "font-medium text-destructive")}>
                {t("okr.my.deadline", "DDL")}: {deadline}
                {isOverdue && ` (${t("okr.my.overdue", "已超期")})`}
              </span>
            </div>

            <div className="mt-3 flex items-center gap-3">
              <Progress value={progress} className="h-2 flex-1" />
              <span className="shrink-0 text-caption text-muted-foreground">
                {progress}%
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default MyKrList
