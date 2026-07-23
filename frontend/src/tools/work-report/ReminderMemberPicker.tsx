import { Search, UsersRound } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import type { DepartmentPublic, ReminderRecipient } from "@/client"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

type SelectionFilter = "all" | "selected" | "unselected"

type ReminderMemberPickerProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  recipients: ReminderRecipient[]
  departments: DepartmentPublic[]
  selectedIds: string[]
  onConfirm: (selectedIds: string[]) => void
}

const ReminderMemberPicker = ({
  open,
  onOpenChange,
  recipients,
  departments,
  selectedIds,
  onConfirm,
}: ReminderMemberPickerProps) => {
  const [keyword, setKeyword] = useState("")
  const [departmentId, setDepartmentId] = useState("all")
  const [selectionFilter, setSelectionFilter] = useState<SelectionFilter>("all")
  const [draftIds, setDraftIds] = useState<string[]>([])

  useEffect(() => {
    if (!open) return
    setKeyword("")
    setDepartmentId("all")
    setSelectionFilter("all")
    setDraftIds(selectedIds)
  }, [open, selectedIds])

  const filteredRecipients = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLocaleLowerCase()
    return recipients.filter((recipient) => {
      const matchesKeyword =
        !normalizedKeyword ||
        (recipient.name ?? "")
          .toLocaleLowerCase()
          .includes(normalizedKeyword) ||
        recipient.email.toLocaleLowerCase().includes(normalizedKeyword)
      const matchesDepartment =
        departmentId === "all" ||
        (departmentId === "none"
          ? !recipient.department_id
          : recipient.department_id === departmentId)
      const isSelected = draftIds.includes(recipient.id)
      const matchesSelection =
        selectionFilter === "all" ||
        (selectionFilter === "selected" && isSelected) ||
        (selectionFilter === "unselected" && !isSelected)
      return matchesKeyword && matchesDepartment && matchesSelection
    })
  }, [departmentId, draftIds, keyword, recipients, selectionFilter])

  const filteredIds = filteredRecipients.map((recipient) => recipient.id)
  const allFilteredSelected =
    filteredIds.length > 0 && filteredIds.every((id) => draftIds.includes(id))

  const toggleFiltered = () => {
    if (allFilteredSelected) {
      setDraftIds((current) =>
        current.filter((id) => !filteredIds.includes(id)),
      )
      return
    }
    setDraftIds((current) => [...new Set([...current, ...filteredIds])])
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[86vh] flex-col sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UsersRound className="h-5 w-5 text-primary" />
            选择发送成员
          </DialogTitle>
          <DialogDescription>
            仅展示启用且已绑定飞书的成员。当前已选择 {draftIds.length} 人。
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-3 sm:grid-cols-[1fr_12rem_10rem]">
          <div className="relative">
            <Search className="absolute top-2.5 left-3 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="搜索姓名或邮箱"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
            />
          </div>
          <select
            aria-label="部门筛选"
            className="border-input bg-background h-9 rounded-md border px-3 text-sm"
            value={departmentId}
            onChange={(event) => setDepartmentId(event.target.value)}
          >
            <option value="all">全部部门</option>
            <option value="none">未分配部门</option>
            {departments.map((department) => (
              <option key={department.id} value={department.id}>
                {department.name}
              </option>
            ))}
          </select>
          <select
            aria-label="选择状态筛选"
            className="border-input bg-background h-9 rounded-md border px-3 text-sm"
            value={selectionFilter}
            onChange={(event) =>
              setSelectionFilter(event.target.value as SelectionFilter)
            }
          >
            <option value="all">全部状态</option>
            <option value="selected">已选择</option>
            <option value="unselected">未选择</option>
          </select>
        </div>

        <div className="flex items-center justify-between gap-3 text-sm">
          <span className="text-muted-foreground">
            当前筛选结果 {filteredRecipients.length} 人
          </span>
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={filteredIds.length === 0}
            onClick={toggleFiltered}
          >
            {allFilteredSelected ? "取消全选" : "全选"}
          </Button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto rounded-md border">
          {filteredRecipients.length === 0 ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              没有符合条件的成员
            </div>
          ) : (
            <div className="divide-y">
              {filteredRecipients.map((recipient) => {
                const checkboxId = `picker-recipient-${recipient.id}`
                const departmentName = recipient.department_id
                  ? departments.find(
                      (department) => department.id === recipient.department_id,
                    )?.name
                  : null
                return (
                  <Label
                    key={recipient.id}
                    htmlFor={checkboxId}
                    className="flex cursor-pointer items-center gap-3 px-4 py-3 font-normal hover:bg-muted/60"
                  >
                    <Checkbox
                      id={checkboxId}
                      checked={draftIds.includes(recipient.id)}
                      onCheckedChange={(checked) =>
                        setDraftIds((current) =>
                          checked === true
                            ? [...new Set([...current, recipient.id])]
                            : current.filter((id) => id !== recipient.id),
                        )
                      }
                    />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium">
                        {recipient.name || recipient.email}
                      </span>
                      <span className="block truncate text-xs text-muted-foreground">
                        {recipient.email}
                      </span>
                    </span>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {departmentName || "未分配部门"}
                    </span>
                  </Label>
                )
              })}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            取消
          </Button>
          <Button
            type="button"
            onClick={() => {
              onConfirm(draftIds)
              onOpenChange(false)
            }}
          >
            确认选择（{draftIds.length}）
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default ReminderMemberPicker
