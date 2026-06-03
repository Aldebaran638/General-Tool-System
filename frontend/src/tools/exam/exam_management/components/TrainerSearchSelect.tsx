import { useState, useEffect, useRef } from "react"
import { useQuery } from "@tanstack/react-query"
import { Loader2, Search, X, Check } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"

import { searchUsers } from "../api"
import type { WecomUser } from "../api"
import type { TrainerInfo } from "../types"

interface TrainerSearchSelectProps {
  selectedTrainerIds: string[]
  selectedTrainers: TrainerInfo[]
  onSelectionChange: (ids: string[]) => void
  disabled?: boolean
}

export function TrainerSearchSelect({
  selectedTrainerIds,
  selectedTrainers,
  onSelectionChange,
  disabled,
}: TrainerSearchSelectProps) {
  const [open, setOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const searchQuery_ = useQuery({
    queryKey: ["trainerSearch", searchQuery],
    queryFn: () => searchUsers({ q: searchQuery || undefined, limit: 20 }),
    enabled: open && searchQuery.length >= 0,
  })

  const users = searchQuery_?.data?.data ?? []
  const isLoading = searchQuery_?.isLoading ?? false

  // Build a map of selected trainer info for display
  const trainerInfoMap = new Map(selectedTrainers.map((t) => [t.id, t.name]))

  // Filter out already selected trainers
  const selectedIds = new Set(selectedTrainerIds)
  const availableUsers = users.filter((u) => !selectedIds.has(u.userid))

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  function handleSelect(user: WecomUser) {
    onSelectionChange([...selectedTrainerIds, user.userid])
    setSearchQuery("")
    inputRef.current?.focus()
  }

  function handleRemove(userid: string) {
    onSelectionChange(selectedTrainerIds.filter((id) => id !== userid))
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      setOpen(false)
    }
  }

  // Resolve display name for a trainer id
  function getTrainerName(id: string): string {
    return trainerInfoMap.get(id) ?? id
  }

  return (
    <div className="flex flex-col gap-2">
      {/* Selected trainer tags */}
      {selectedTrainerIds.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedTrainerIds.map((id) => (
            <Badge key={id} variant="secondary" className="pr-1">
              <span className="mr-1">{getTrainerName(id)}</span>
              {!disabled && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-4 w-4 ml-1 hover:bg-destructive/20"
                  onClick={() => handleRemove(id)}
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
            </Badge>
          ))}
        </div>
      )}

      {/* Search input with dropdown */}
      <div ref={containerRef} className="relative">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            ref={inputRef}
            placeholder="输入姓名搜索讲师..."
            value={searchQuery}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
              setSearchQuery(e.target.value)
              if (!open) setOpen(true)
            }}
            onFocus={() => setOpen(true)}
            onKeyDown={handleKeyDown}
            className="pl-8"
            disabled={disabled}
          />
          {searchQuery && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1 h-7 w-7"
              onClick={() => {
                setSearchQuery("")
                inputRef.current?.focus()
              }}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Dropdown */}
        {open && (
          <div className="absolute z-50 mt-1 w-full rounded-md border bg-popover shadow-md">
            <div className="max-h-[300px] overflow-auto p-1">
              {isLoading && (
                <div className="flex items-center justify-center py-6 text-sm text-muted-foreground">
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  搜索中...
                </div>
              )}
              {!isLoading && availableUsers.length === 0 && (
                <div className="py-6 text-center text-sm text-muted-foreground">
                  {searchQuery ? "未找到匹配的用户" : "请输入关键词搜索"}
                </div>
              )}
              {!isLoading &&
                availableUsers.map((user) => (
                  <div
                    key={user.userid}
                    className="flex cursor-pointer items-center justify-between rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground"
                    onClick={() => handleSelect(user)}
                  >
                    <div className="flex flex-col">
                      <span className="font-medium">{user.name}</span>
                      <span className="text-xs text-muted-foreground">
                        {user.userid}
                      </span>
                    </div>
                    <Check className="h-4 w-4 opacity-0" />
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
