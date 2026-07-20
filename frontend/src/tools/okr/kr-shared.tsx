import { useTranslation } from "react-i18next"
import type { KeyResultPublic } from "@/client"
import { Progress } from "@/components/ui/progress"

export function formatKrDate(value: string | null | undefined) {
  if (!value) return "-"
  return value.slice(0, 10)
}

interface KrTableProps {
  krs: KeyResultPublic[]
  showAssignee?: boolean
  showDepartment?: boolean
}

/**
 * Shared KR listing for the OKR boards. Columns: title, description,
 * optional assignee, optional department, start date, deadline and a
 * progress bar with percentage. The caller is responsible for wrapping the
 * table in a horizontal scroll container when space is tight.
 */
export function KrTable({
  krs,
  showAssignee = false,
  showDepartment = false,
}: KrTableProps) {
  const { t } = useTranslation()

  const gridTemplateColumns = [
    "minmax(0,2fr)",
    "minmax(0,2fr)",
    showAssignee ? "minmax(0,1fr)" : null,
    showDepartment ? "minmax(0,1fr)" : null,
    "minmax(0,1fr)",
    "minmax(0,1fr)",
    "minmax(0,1.5fr)",
  ]
    .filter((column): column is string => Boolean(column))
    .join(" ")

  const headers = [
    t("okr.krTitle", "名称"),
    t("okr.krDescription", "详情"),
    ...(showAssignee ? [t("okr.assignee", "人员")] : []),
    ...(showDepartment ? [t("okr.krTable.department", "部门")] : []),
    t("okr.startDate", "开始时间"),
    t("okr.deadline", "DDL"),
    t("okr.progress.label", "进度"),
  ]

  return (
    <div className="min-w-[720px]">
      <div
        className="grid items-center gap-3 border-b border-border px-4 py-2 text-caption text-muted-foreground"
        style={{ gridTemplateColumns }}
      >
        {headers.map((header) => (
          <span key={header} className="truncate">
            {header}
          </span>
        ))}
      </div>
      {krs.map((kr) => {
        const progress = Math.round(kr.progress ?? 0)
        return (
          <div
            key={kr.id}
            className="grid items-center gap-3 border-b border-border px-4 py-2.5 last:border-b-0"
            style={{ gridTemplateColumns }}
          >
            <span className="truncate text-body text-foreground">
              {kr.title}
            </span>
            <span
              className="truncate text-body text-muted-foreground"
              title={kr.description ?? undefined}
            >
              {kr.description || "-"}
            </span>
            {showAssignee && (
              <span className="truncate text-body text-muted-foreground">
                {kr.assignee.full_name || kr.assignee.email}
              </span>
            )}
            {showDepartment && (
              <span className="truncate text-body text-muted-foreground">
                {kr.department?.name ?? "-"}
              </span>
            )}
            <span className="text-body text-muted-foreground">
              {formatKrDate(kr.start_date)}
            </span>
            <span className="text-body text-muted-foreground">
              {formatKrDate(kr.deadline)}
            </span>
            <span className="flex items-center gap-2">
              <Progress value={progress} className="h-2 flex-1" />
              <span className="w-10 text-right text-body text-muted-foreground">
                {progress}%
              </span>
            </span>
          </div>
        )
      })}
    </div>
  )
}
