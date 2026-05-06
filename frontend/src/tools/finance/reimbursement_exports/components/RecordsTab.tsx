import { useState, useMemo } from "react"

import { FileSpreadsheet, Search } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { DatePicker } from "@/components/ui/date-picker"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { useI18n } from "@/i18n/I18nProvider"

import {
  useRecordsQuery,
} from "../hooks/useReimbursementExports"
import type { RecordsQuery, PurchaseRecordWithExportInfo } from "../types"
import { CATEGORY_OPTIONS, EXPORTED_FILTER_OPTIONS } from "../schemas"
import { GenerateDialog } from "./GenerateDialog"

export function RecordsTab() {
  const { t } = useI18n()
  const [filters, setFilters] = useState<RecordsQuery>({ limit: 100 })
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [generateOpen, setGenerateOpen] = useState(false)

  const { data, isLoading, error } = useRecordsQuery(filters)

  const records = data?.data ?? []
  const count = data?.count ?? 0

  const selectedRecords = useMemo(
    () => records.filter((r) => selectedIds.has(r.id)),
    [records, selectedIds],
  )

  const handleToggle = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleToggleAll = () => {
    if (selectedIds.size === records.length && records.length > 0) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(records.map((r) => r.id)))
    }
  }

  const updateFilter = <K extends keyof RecordsQuery>(
    key: K,
    value: RecordsQuery[K],
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
    setSelectedIds(new Set())
  }

  if (error) {
    const status = (error as any)?.status
    if (status === 403) {
      return (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <h3 className="text-lg font-semibold">
            {t("finance.reimbursementExports.errors.forbidden")}
          </h3>
          <p className="text-muted-foreground">
            {t("finance.reimbursementExports.errors.adminRequired")}
          </p>
        </div>
      )
    }
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <h3 className="text-lg font-semibold">
          {t("finance.reimbursementExports.errors.loadFailed")}
        </h3>
        <p className="text-muted-foreground">{(error as Error).message}</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <Input
          placeholder={t("finance.reimbursementExports.filters.q")}
          className="w-48"
          value={filters.q ?? ""}
          onChange={(e) => updateFilter("q", e.target.value || undefined)}
        />
        <DatePicker
          value={filters.start_date}
          onChange={(v) => updateFilter("start_date", v)}
        />
        <DatePicker
          value={filters.end_date}
          onChange={(v) => updateFilter("end_date", v)}
        />
        <Select
          value={filters.category ?? "__all__"}
          onValueChange={(v) => updateFilter("category", v === "__all__" ? undefined : v)}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder={t("finance.reimbursementExports.filters.category")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">
              {t("finance.reimbursementExports.filters.allCategories")}
            </SelectItem>
            {CATEGORY_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {t(opt.labelKey)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={filters.currency ?? "__all__"}
          onValueChange={(v) => updateFilter("currency", v === "__all__" ? undefined : v)}
        >
          <SelectTrigger className="w-32">
            <SelectValue placeholder={t("finance.reimbursementExports.filters.currency")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">
              {t("finance.reimbursementExports.filters.allCurrencies")}
            </SelectItem>
            <SelectItem value="CNY">CNY</SelectItem>
            <SelectItem value="USD">USD</SelectItem>
            <SelectItem value="EUR">EUR</SelectItem>
            <SelectItem value="JPY">JPY</SelectItem>
            <SelectItem value="HKD">HKD</SelectItem>
            <SelectItem value="GBP">GBP</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={filters.exported ?? "all"}
          onValueChange={(v) =>
            updateFilter("exported", v === "all" ? undefined : (v as RecordsQuery["exported"]))
          }
        >
          <SelectTrigger className="w-36">
            <SelectValue placeholder={t("finance.reimbursementExports.filters.exported")} />
          </SelectTrigger>
          <SelectContent>
            {EXPORTED_FILTER_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {t(opt.labelKey)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-muted-foreground text-sm">
          {t("finance.reimbursementExports.records.selectedCount").replace(
            "{count}",
            String(selectedIds.size),
          )}
        </span>
        <Button
          disabled={selectedIds.size === 0}
          onClick={() => setGenerateOpen(true)}
        >
          <FileSpreadsheet className="mr-2 h-4 w-4" />
          {t("finance.reimbursementExports.actions.generate")}
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : records.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="mb-4 rounded-full bg-muted p-4">
            <Search className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold">
            {t("finance.reimbursementExports.empty.recordsTitle")}
          </h3>
          <p className="text-muted-foreground">
            {t("finance.reimbursementExports.empty.recordsDescription")}
          </p>
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <Checkbox
                    checked={
                      records.length > 0 && selectedIds.size === records.length
                    }
                    onCheckedChange={handleToggleAll}
                  />
                </TableHead>
                <TableHead>
                  {t("finance.reimbursementExports.columns.purchaseDate")}
                </TableHead>
                <TableHead>
                  {t("finance.reimbursementExports.columns.orderName")}
                </TableHead>
                <TableHead>
                  {t("finance.reimbursementExports.columns.category")}
                </TableHead>
                <TableHead>
                  {t("finance.reimbursementExports.columns.amount")}
                </TableHead>
                <TableHead>
                  {t("finance.reimbursementExports.columns.currency")}
                </TableHead>
                <TableHead>
                  {t("finance.reimbursementExports.columns.invoiceNumber")}
                </TableHead>
                <TableHead>
                  {t("finance.reimbursementExports.columns.exported")}
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {records.map((record) => (
                <RecordRow
                  key={record.id}
                  record={record}
                  selected={selectedIds.has(record.id)}
                  onToggle={() => handleToggle(record.id)}
                />
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <div className="text-muted-foreground text-sm">
        {t("finance.reimbursementExports.records.total").replace("{count}", String(count))}
      </div>

      <GenerateDialog
        open={generateOpen}
        onClose={() => setGenerateOpen(false)}
        selectedRecords={selectedRecords}
        onSuccess={() => setSelectedIds(new Set())}
      />
    </div>
  )
}

function RecordRow({
  record,
  selected,
  onToggle,
}: {
  record: PurchaseRecordWithExportInfo
  selected: boolean
  onToggle: () => void
}) {
  const { t } = useI18n()

  return (
    <TableRow>
      <TableCell>
        <Checkbox checked={selected} onCheckedChange={onToggle} />
      </TableCell>
      <TableCell>{record.purchase_date}</TableCell>
      <TableCell className="font-medium">{record.order_name}</TableCell>
      <TableCell>{t(`finance.purchaseRecords.category.${record.category}` as any) || record.category}</TableCell>
      <TableCell>{record.amount}</TableCell>
      <TableCell>{record.currency}</TableCell>
      <TableCell>
        {record.invoice_file?.invoice_number ?? "—"}
      </TableCell>
      <TableCell>
        {record.exported ? (
          <Badge variant="secondary">
            {t("finance.reimbursementExports.status.exported")}
          </Badge>
        ) : (
          <Badge variant="outline">
            {t("finance.reimbursementExports.status.notExported")}
          </Badge>
        )}
      </TableCell>
    </TableRow>
  )
}
