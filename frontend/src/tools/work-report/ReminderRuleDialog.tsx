import { BellRing, UsersRound } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import type {
  DepartmentPublic,
  ReminderRecipient,
  ReminderRuleInput,
  ReminderRulePublic,
} from "@/client"
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
import { LoadingButton } from "@/components/ui/loading-button"
import ReminderMemberPicker from "./ReminderMemberPicker"

const WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

type RuleDraft = {
  report_type: "weekly" | "monthly"
  weekday: number
  month_day: number
  is_last_day: boolean
  local_time: string
  timezone: string
  enabled: boolean
  recipient_user_ids: string[]
}

const emptyDraft = (): RuleDraft => ({
  report_type: "weekly",
  weekday: 5,
  month_day: 28,
  is_last_day: false,
  local_time: "17:00",
  timezone: "Asia/Shanghai",
  enabled: true,
  recipient_user_ids: [],
})

const payloadFromDraft = (draft: RuleDraft): ReminderRuleInput => ({
  report_type: draft.report_type,
  weekday: draft.report_type === "weekly" ? draft.weekday : null,
  month_day:
    draft.report_type === "monthly" && !draft.is_last_day
      ? draft.month_day
      : null,
  is_last_day: draft.report_type === "monthly" && draft.is_last_day,
  local_time: draft.local_time,
  timezone: draft.timezone,
  enabled: draft.enabled,
  recipient_user_ids: draft.recipient_user_ids,
})

type ReminderRuleDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  rule: ReminderRulePublic | null
  recipients: ReminderRecipient[]
  departments: DepartmentPublic[]
  timezones: string[]
  saving: boolean
  onSave: (payload: ReminderRuleInput) => void
}

const ReminderRuleDialog = ({
  open,
  onOpenChange,
  rule,
  recipients,
  departments,
  timezones,
  saving,
  onSave,
}: ReminderRuleDialogProps) => {
  const [draft, setDraft] = useState<RuleDraft>(emptyDraft)
  const [memberPickerOpen, setMemberPickerOpen] = useState(false)

  useEffect(() => {
    if (!open) return
    const availableIds = new Set(recipients.map((recipient) => recipient.id))
    setDraft(
      rule
        ? {
            report_type: rule.report_type,
            weekday: rule.weekday ?? 5,
            month_day: rule.month_day ?? 28,
            is_last_day: rule.is_last_day ?? false,
            local_time: rule.local_time.slice(0, 5),
            timezone: rule.timezone ?? "Asia/Shanghai",
            enabled: rule.enabled ?? true,
            recipient_user_ids: (rule.recipient_user_ids ?? []).filter((id) =>
              availableIds.has(id),
            ),
          }
        : emptyDraft(),
    )
    setMemberPickerOpen(false)
  }, [open, recipients, rule])

  const selectedNames = useMemo(
    () =>
      draft.recipient_user_ids
        .map((id) => recipients.find((recipient) => recipient.id === id))
        .filter((recipient) => Boolean(recipient))
        .map((recipient) => recipient?.name || recipient?.email),
    [draft.recipient_user_ids, recipients],
  )

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="flex max-h-[90vh] flex-col sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <BellRing className="h-5 w-5 text-primary" />
              {rule ? "编辑提醒规则" : "新增提醒规则"}
            </DialogTitle>
            <DialogDescription>
              设置发送时间和适用成员。触发时只提醒尚未提交对应汇报的成员。
            </DialogDescription>
          </DialogHeader>

          <div className="grid min-h-0 flex-1 gap-4 overflow-y-auto pr-1 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="rule-report-type">汇报类型</Label>
              <select
                id="rule-report-type"
                className="border-input bg-background h-9 w-full rounded-md border px-3 text-sm"
                value={draft.report_type}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,
                    report_type: event.target.value as "weekly" | "monthly",
                  }))
                }
              >
                <option value="weekly">周报</option>
                <option value="monthly">月报</option>
              </select>
            </div>

            {draft.report_type === "weekly" ? (
              <div className="space-y-2">
                <Label htmlFor="rule-weekday">星期</Label>
                <select
                  id="rule-weekday"
                  className="border-input bg-background h-9 w-full rounded-md border px-3 text-sm"
                  value={draft.weekday}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      weekday: Number(event.target.value),
                    }))
                  }
                >
                  {WEEKDAYS.map((label, index) => (
                    <option key={label} value={index + 1}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="space-y-2">
                <Label htmlFor="rule-month-mode">日期</Label>
                <div className="flex gap-2">
                  <select
                    id="rule-month-mode"
                    className="border-input bg-background h-9 min-w-32 rounded-md border px-3 text-sm"
                    value={draft.is_last_day ? "last" : "fixed"}
                    onChange={(event) =>
                      setDraft((current) => ({
                        ...current,
                        is_last_day: event.target.value === "last",
                      }))
                    }
                  >
                    <option value="fixed">固定日期</option>
                    <option value="last">最后一天</option>
                  </select>
                  {!draft.is_last_day ? (
                    <Input
                      type="number"
                      min={1}
                      max={31}
                      value={draft.month_day}
                      onChange={(event) =>
                        setDraft((current) => ({
                          ...current,
                          month_day: Number(event.target.value),
                        }))
                      }
                      aria-label="每月日期"
                    />
                  ) : null}
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="rule-time">时间</Label>
              <Input
                id="rule-time"
                type="time"
                value={draft.local_time}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,
                    local_time: event.target.value,
                  }))
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="rule-timezone">时区</Label>
              <Input
                id="rule-timezone"
                list="rule-timezones"
                value={draft.timezone}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,
                    timezone: event.target.value,
                  }))
                }
              />
              <datalist id="rule-timezones">
                {timezones.map((timezone) => (
                  <option key={timezone} value={timezone} />
                ))}
              </datalist>
            </div>

            <div className="space-y-2 md:col-span-2">
              <Label>发送成员</Label>
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border p-4">
                <div className="min-w-0">
                  <p className="text-sm font-medium">
                    已选择 {draft.recipient_user_ids.length} 人
                  </p>
                  <p className="mt-1 truncate text-xs text-muted-foreground">
                    {selectedNames.length
                      ? selectedNames.slice(0, 4).join("、")
                      : "尚未选择发送成员"}
                    {selectedNames.length > 4
                      ? ` 等 ${selectedNames.length} 人`
                      : ""}
                  </p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setMemberPickerOpen(true)}
                >
                  <UsersRound className="h-4 w-4" />
                  选择成员
                </Button>
              </div>
            </div>

            <div className="flex items-center gap-2 md:col-span-2">
              <Checkbox
                id="rule-enabled"
                checked={draft.enabled}
                onCheckedChange={(checked) =>
                  setDraft((current) => ({
                    ...current,
                    enabled: checked === true,
                  }))
                }
              />
              <Label htmlFor="rule-enabled">保存后立即启用</Label>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              disabled={saving}
              onClick={() => onOpenChange(false)}
            >
              取消
            </Button>
            <LoadingButton
              disabled={draft.recipient_user_ids.length === 0}
              loading={saving}
              onClick={() => onSave(payloadFromDraft(draft))}
            >
              保存规则
            </LoadingButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ReminderMemberPicker
        open={memberPickerOpen}
        onOpenChange={setMemberPickerOpen}
        recipients={recipients}
        departments={departments}
        selectedIds={draft.recipient_user_ids}
        onConfirm={(recipientUserIds) =>
          setDraft((current) => ({
            ...current,
            recipient_user_ids: recipientUserIds,
          }))
        }
      />
    </>
  )
}

export default ReminderRuleDialog
