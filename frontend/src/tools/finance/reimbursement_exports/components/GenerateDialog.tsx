import { useMemo, useState } from "react"

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
import { DatePicker } from "@/components/ui/date-picker"
import { Label } from "@/components/ui/label"
import { useI18n } from "@/i18n/I18nProvider"

import { useGenerateExportMutation } from "../hooks/useReimbursementExports"
import type { PurchaseRecordWithExportInfo } from "../types"

interface GenerateDialogProps {
  open: boolean
  onClose: () => void
  selectedRecords: PurchaseRecordWithExportInfo[]
  onSuccess: () => void
}

export function GenerateDialog({
  open,
  onClose,
  selectedRecords,
  onSuccess,
}: GenerateDialogProps) {
  const { t } = useI18n()
  const [department, setDepartment] = useState("")
  const [businessUnit, setBusinessUnit] = useState("")
  const [reimburser, setReimburser] = useState("")
  const [reimbursementDate, setReimbursementDate] = useState<string | undefined>("")
  const [retentionDays, setRetentionDays] = useState("")

  const generateMutation = useGenerateExportMutation()

  const currencies = useMemo(
    () => [...new Set(selectedRecords.map((r) => r.currency))],
    [selectedRecords],
  )
  const hasMultipleCurrencies = currencies.length > 1
  const hasExported = selectedRecords.some((r) => r.exported)

  const handleSubmit = async () => {
    if (hasMultipleCurrencies) return

    if (hasExported) {
      const confirmed = window.confirm(
        t("finance.reimbursementExports.warnings.reExportConfirm"),
      )
      if (!confirmed) return
    }

    await generateMutation.mutateAsync({
      purchase_record_ids: selectedRecords.map((r) => r.id),
      department: department || null,
      business_unit: businessUnit || null,
      reimburser: reimburser || null,
      reimbursement_date: reimbursementDate || null,
      retention_days: retentionDays ? Number(retentionDays) : null,
    })

    onSuccess()
    onClose()
    setDepartment("")
    setBusinessUnit("")
    setReimburser("")
    setReimbursementDate("")
    setRetentionDays("")
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {t("finance.reimbursementExports.generate.title")}
          </DialogTitle>
          <DialogDescription>
            {t("finance.reimbursementExports.generate.description").replace(
              "{count}",
              String(selectedRecords.length),
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-2">
          {hasMultipleCurrencies && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {t("finance.reimbursementExports.errors.multipleCurrencies")}
            </div>
          )}

          {hasExported && !hasMultipleCurrencies && (
            <div className="rounded-md bg-amber-50 p-3 text-sm text-amber-800">
              {t("finance.reimbursementExports.warnings.containsExported")}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <Label>{t("finance.reimbursementExports.generate.department")}</Label>
              <Input
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                placeholder={t("finance.reimbursementExports.generate.departmentPlaceholder")}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label>{t("finance.reimbursementExports.generate.businessUnit")}</Label>
              <Input
                value={businessUnit}
                onChange={(e) => setBusinessUnit(e.target.value)}
                placeholder={t("finance.reimbursementExports.generate.businessUnitPlaceholder")}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <Label>{t("finance.reimbursementExports.generate.reimburser")}</Label>
              <Input
                value={reimburser}
                onChange={(e) => setReimburser(e.target.value)}
                placeholder={t("finance.reimbursementExports.generate.reimburserPlaceholder")}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label>{t("finance.reimbursementExports.generate.reimbursementDate")}</Label>
              <DatePicker
                value={reimbursementDate}
                onChange={setReimbursementDate}
              />
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Label>{t("finance.reimbursementExports.generate.retentionDays")}</Label>
            <Input
              type="number"
              min={1}
              max={365}
              value={retentionDays}
              onChange={(e) => setRetentionDays(e.target.value)}
              placeholder={t("finance.reimbursementExports.generate.retentionDaysPlaceholder")}
            />
            <p className="text-muted-foreground text-xs">
              {t("finance.reimbursementExports.generate.retentionDaysHint")}
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={generateMutation.isPending || hasMultipleCurrencies || selectedRecords.length === 0}
          >
            {generateMutation.isPending
              ? t("finance.reimbursementExports.generate.submitting")
              : t("finance.reimbursementExports.actions.generate")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
