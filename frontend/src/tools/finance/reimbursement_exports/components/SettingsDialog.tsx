import { useEffect, useState } from "react"

import { Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
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
import { useI18n } from "@/i18n/I18nProvider"

import {
  useSettingsQuery,
  useUpdateSettingsMutation,
  usePurgeExpiredFilesMutation,
} from "../hooks/useReimbursementExports"

interface SettingsDialogProps {
  open: boolean
  onClose: () => void
}

export function SettingsDialog({ open, onClose }: SettingsDialogProps) {
  const { t } = useI18n()
  const { data: settings, isLoading } = useSettingsQuery()
  const updateMutation = useUpdateSettingsMutation()
  const purgeMutation = usePurgeExpiredFilesMutation()

  const [retentionDays, setRetentionDays] = useState("")

  useEffect(() => {
    if (settings) {
      setRetentionDays(String(settings.retention_days))
    }
  }, [settings])

  const handleSave = async () => {
    const days = Number(retentionDays)
    if (Number.isNaN(days) || days < 1 || days > 365) {
      alert(t("finance.reimbursementExports.errors.retentionDaysRange"))
      return
    }
    await updateMutation.mutateAsync({ retention_days: days })
    onClose()
  }

  const handlePurge = async () => {
    const confirmed = window.confirm(
      t("finance.reimbursementExports.purge.confirm"),
    )
    if (!confirmed) return
    await purgeMutation.mutateAsync()
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {t("finance.reimbursementExports.settings.title")}
          </DialogTitle>
          <DialogDescription>
            {t("finance.reimbursementExports.settings.description")}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        ) : (
          <div className="flex flex-col gap-6 py-2">
            <div className="flex flex-col gap-2">
              <Label htmlFor="retention-days">
                {t("finance.reimbursementExports.settings.retentionDays")}
              </Label>
              <Input
                id="retention-days"
                type="number"
                min={1}
                max={365}
                value={retentionDays}
                onChange={(e) => setRetentionDays(e.target.value)}
              />
              <p className="text-muted-foreground text-xs">
                {t("finance.reimbursementExports.settings.retentionDaysHint")}
              </p>
            </div>

            <div className="flex flex-col gap-2">
              <Label>{t("finance.reimbursementExports.purge.title")}</Label>
              <Button
                variant="destructive"
                onClick={handlePurge}
                disabled={purgeMutation.isPending}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                {purgeMutation.isPending
                  ? t("finance.reimbursementExports.purge.purging")
                  : t("finance.reimbursementExports.purge.button")}
              </Button>
              <p className="text-muted-foreground text-xs">
                {t("finance.reimbursementExports.purge.description")}
              </p>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button
            onClick={handleSave}
            disabled={updateMutation.isPending || isLoading}
          >
            {updateMutation.isPending
              ? t("finance.reimbursementExports.settings.saving")
              : t("common.save")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
