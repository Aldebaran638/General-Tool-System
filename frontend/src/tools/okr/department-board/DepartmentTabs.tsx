import { useState } from "react"
import { useTranslation } from "react-i18next"
import type { DepartmentStats } from "@/client"
import { cn } from "@/lib/utils"

export const ALL_DEPARTMENTS_ID = "__all_departments__"

const SELECTED_Z_INDEX = 100
const HOVERED_Z_INDEX = 200

interface DepartmentTabsProps {
  departments: DepartmentStats[]
  selectedId: string
  onSelect: (id: string) => void
}

/**
 * Overlapping fixed-width tabs.
 *
 * Every tab is 180px wide regardless of the department name. Starting from
 * the second tab, each tab overlaps the previous one by 28px via a negative
 * left margin, and z-index rises from left to right so a tab always covers
 * the right edge of its predecessor. The selected tab sits above all others
 * and merges with the content panel below; hovering any other tab lifts it
 * to the very top and nudges it up by 4px so it can be read in full.
 */
export function DepartmentTabs({
  departments,
  selectedId,
  onSelect,
}: DepartmentTabsProps) {
  const { t } = useTranslation()
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  const tabs = [
    { id: ALL_DEPARTMENTS_ID, name: t("okr.allDepartments", "全部部门") },
    ...departments.map((stats) => ({
      id: stats.department.id,
      name: stats.department.name,
    })),
  ]

  return (
    <div
      role="tablist"
      aria-label={t("okr.allDepartments", "全部部门")}
      className="relative z-10 -mb-px overflow-x-auto pt-2"
    >
      <div className="flex w-max">
        {tabs.map((tab, index) => {
          const isSelected = tab.id === selectedId
          const isHovered = tab.id === hoveredId
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isSelected}
              title={tab.name}
              onClick={() => onSelect(tab.id)}
              onMouseEnter={() => setHoveredId(tab.id)}
              onMouseLeave={() => setHoveredId(null)}
              className={cn(
                "text-body relative h-11 w-[180px] flex-shrink-0 rounded-t-lg border border-b-0 border-border px-4 text-left transition-all duration-200",
                index > 0 && "ml-[-28px]",
                isSelected
                  ? "bg-card text-foreground"
                  : "bg-muted/70 text-muted-foreground hover:bg-muted hover:text-foreground",
                isHovered && !isSelected && "-translate-y-1",
              )}
              style={{
                zIndex: isHovered
                  ? HOVERED_Z_INDEX
                  : isSelected
                    ? SELECTED_Z_INDEX
                    : index,
              }}
            >
              <span className="block truncate">{tab.name}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
