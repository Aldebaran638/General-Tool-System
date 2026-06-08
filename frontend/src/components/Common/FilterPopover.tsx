import { Filter } from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export type FilterOption = { label: string; value: string }

export type FilterGroup =
  | {
      key: string
      label: string
      type: "single"
      options: FilterOption[]
    }
  | {
      key: string
      label: string
      type: "multi"
      options: FilterOption[]
    }

export type FilterValues = Record<string, string | string[]>

interface FilterPopoverProps {
  groups: FilterGroup[]
  values: FilterValues
  onChange: (values: FilterValues) => void
}

export function FilterPopover({ groups, values, onChange }: FilterPopoverProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [draftValues, setDraftValues] = useState<FilterValues>(values)
  const wrapperRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isOpen) return

    function handleClick(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    function handleKeydown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false)
      }
    }

    document.addEventListener("mousedown", handleClick)
    document.addEventListener("keydown", handleKeydown)
    return () => {
      document.removeEventListener("mousedown", handleClick)
      document.removeEventListener("keydown", handleKeydown)
    }
  }, [isOpen])

  const activeCount = useMemo(() => {
    return groups.reduce((count, group) => {
      const val = values[group.key]
      if (group.type === "single") {
        const firstValue = group.options[0]?.value ?? ""
        if (val && val !== firstValue) count++
      } else if (Array.isArray(val) && val.length > 0) {
        count++
      }
      return count
    }, 0)
  }, [groups, values])

  function open() {
    setDraftValues({ ...values })
    setIsOpen(true)
  }

  function apply() {
    onChange({ ...draftValues })
    setIsOpen(false)
  }

  function reset() {
    const defaults: FilterValues = {}
    for (const group of groups) {
      defaults[group.key] = group.type === "single" ? "" : []
    }
    setDraftValues(defaults)
  }

  function toggleMulti(key: string, optionValue: string) {
    setDraftValues((prev) => {
      const current = (prev[key] as string[]) || []
      if (current.includes(optionValue)) {
        return { ...prev, [key]: current.filter((v) => v !== optionValue) }
      }
      return { ...prev, [key]: [...current, optionValue] }
    })
  }

  return (
    <div className="relative inline-block" ref={wrapperRef}>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => {
          if (isOpen) {
            setIsOpen(false)
          } else {
            open()
          }
        }}
        className="gap-1.5"
      >
        <Filter className="h-4 w-4" />
        <span>筛选</span>
        {activeCount > 0 && (
          <span className="ml-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-destructive px-1.5 text-[11px] font-bold text-destructive-foreground">
            {activeCount}
          </span>
        )}
      </Button>

      {isOpen && (
        <div
          className="absolute left-0 top-[calc(100%+8px)] z-50 flex w-80 max-w-[90vw] flex-col rounded-xl border bg-popover text-popover-foreground shadow-lg"
          role="dialog"
          aria-label="筛选条件"
        >
          <div className="flex items-center justify-between gap-3 border-b px-4 py-3">
            <span className="text-sm font-semibold">筛选条件</span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={reset}
                className="h-7 rounded-md bg-secondary px-2.5 text-xs font-medium text-secondary-foreground transition-colors hover:bg-secondary/80"
              >
                重置
              </button>
              <button
                type="button"
                onClick={apply}
                className="h-7 rounded-md bg-primary px-3 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90"
              >
                应用
              </button>
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto p-4">
            {groups.map((group) => (
              <div key={group.key} className="mb-4 last:mb-0">
                <span className="mb-2 block text-xs font-medium text-muted-foreground">
                  {group.label}
                </span>
                <div className="flex flex-wrap gap-2">
                  {group.options.map((option) => {
                    const isActive =
                      group.type === "single"
                        ? (draftValues[group.key] as string) === option.value
                        : ((draftValues[group.key] as string[]) || []).includes(option.value)

                    return (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => {
                          if (group.type === "single") {
                            setDraftValues((prev) => ({
                              ...prev,
                              [group.key]: option.value,
                            }))
                          } else {
                            toggleMulti(group.key, option.value)
                          }
                        }}
                        className={cn(
                          "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                          isActive
                            ? "border-primary bg-primary/10 text-primary"
                            : "border-input bg-background text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                        )}
                      >
                        {option.label}
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
