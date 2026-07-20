import { ChevronRight } from "lucide-react"
import { useTranslation } from "react-i18next"
import type { UserStats } from "@/client"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import { KrTable } from "@/tools/okr/kr-shared"

export const userRowGridColumns =
  "grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)_minmax(0,0.8fr)_minmax(0,1.5fr)_auto]"

interface UserRowProps {
  stats: UserStats
  open: boolean
  onToggle: () => void
}

/**
 * A single member row on the people board. Clicking the row expands it with
 * a smooth grid-rows 0fr -> 1fr transition (same pattern as the sidebar
 * groups) to reveal every KR the member is responsible for.
 */
export function UserRow({ stats, open, onToggle }: UserRowProps) {
  const { t } = useTranslation()
  const avg = Math.round(stats.avg_progress)

  return (
    <div className="rounded-lg border border-border bg-card">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className={cn(
          "grid w-full items-center gap-3 rounded-lg px-4 py-3 text-left transition-colors hover:bg-muted/50",
          userRowGridColumns,
        )}
      >
        <span className="truncate text-body text-foreground">
          {stats.user.full_name || stats.user.email}
        </span>
        <span className="truncate text-body text-muted-foreground">
          {stats.department?.name ?? "-"}
        </span>
        <span className="text-body text-muted-foreground">
          {stats.kr_count}
        </span>
        <span className="flex items-center gap-2">
          <Progress value={avg} className="h-2 flex-1" />
          <span className="w-10 text-right text-body text-muted-foreground">
            {avg}%
          </span>
        </span>
        <ChevronRight
          className={cn(
            "size-4 text-muted-foreground transition-transform duration-300 ease-out",
            open && "rotate-90",
          )}
        />
      </button>
      <div
        className={cn(
          "grid min-h-0 transition-[grid-template-rows,opacity] duration-300 ease-out",
          open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0",
        )}
      >
        <div className="min-h-0 overflow-hidden">
          <div className="border-t border-border px-2 py-3">
            {stats.krs.length === 0 ? (
              <p className="px-2 text-body text-muted-foreground">
                {t("okr.noKrs", "暂无 KR")}
              </p>
            ) : (
              <div className="overflow-x-auto">
                <KrTable krs={stats.krs} showDepartment />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
