import { ChevronRight, Pencil, Plus } from "lucide-react"
import { useState } from "react"
import { useTranslation } from "react-i18next"

import type { ObjectivePublic } from "@/client"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import DeleteObjective from "@/tools/okr/overview/DeleteObjective"
import KrForm from "@/tools/okr/overview/KrForm"
import KrTable from "@/tools/okr/overview/KrTable"
import ObjectiveForm from "@/tools/okr/overview/ObjectiveForm"

interface ObjectiveCardProps {
  objective: ObjectivePublic
}

const ObjectiveCard = ({ objective }: ObjectiveCardProps) => {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)

  const progress = Math.round(objective.progress ?? 0)
  const timeRange = objective.time_range

  const toggle = () => setExpanded((prev) => !prev)

  return (
    <div className="rounded-lg border border-border bg-card text-card-foreground shadow-sm">
      <div className="flex items-center gap-4 p-4">
        {/* 折叠态一行：点击展开/收起 */}
        <button
          type="button"
          aria-expanded={expanded}
          onClick={toggle}
          className="flex min-w-0 flex-1 cursor-pointer items-center gap-4 text-left"
        >
          <ChevronRight
            className={cn(
              "h-5 w-5 shrink-0 text-muted-foreground transition-transform duration-300 ease-out",
              expanded && "rotate-90",
            )}
          />

          <span className="min-w-0 flex-1">
            <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="truncate text-subheading">
                {objective.title}
              </span>
              <span className="shrink-0 text-caption text-muted-foreground">
                {t("okr.card.krCount", "{{count}} 个 KR", {
                  count: objective.kr_count ?? 0,
                })}
              </span>
              {timeRange && (
                <span className="shrink-0 text-caption text-muted-foreground">
                  {timeRange.start.slice(0, 10)} ~ {timeRange.end.slice(0, 10)}
                </span>
              )}
            </span>
            {objective.description && (
              <span className="mt-1 block truncate text-caption text-muted-foreground">
                {objective.description}
              </span>
            )}
            <span className="mt-2 flex items-center gap-3">
              <Progress value={progress} className="h-2 max-w-md flex-1" />
              <span className="shrink-0 text-caption text-muted-foreground">
                {progress}%
              </span>
            </span>
          </span>
        </button>

        {/* 超管操作 */}
        <span className="flex shrink-0 items-center gap-1">
          <KrForm
            objectiveId={objective.id}
            trigger={
              <Button variant="outline" size="sm">
                <Plus className="mr-1 h-4 w-4" />
                {t("okr.card.addKr", "添加 KR")}
              </Button>
            }
          />
          <ObjectiveForm
            objective={objective}
            trigger={
              <Button
                variant="ghost"
                size="icon"
                className="text-muted-foreground"
                aria-label={t("okr.card.edit", "编辑目标")}
              >
                <Pencil className="h-4 w-4" />
              </Button>
            }
          />
          <DeleteObjective id={objective.id} title={objective.title} />
        </span>
      </div>

      {/* 展开态：grid-rows 0fr -> 1fr 平滑动画，内容淡入 */}
      <div
        className={cn(
          "grid min-h-0 transition-[grid-template-rows,opacity] duration-300 ease-out",
          expanded
            ? "grid-rows-[1fr] opacity-100"
            : "grid-rows-[0fr] opacity-0",
        )}
      >
        <div className="min-h-0 overflow-hidden">
          <div className="border-t border-border px-4 pb-4 pt-3">
            <KrTable objectiveId={objective.id} enabled={expanded} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default ObjectiveCard
