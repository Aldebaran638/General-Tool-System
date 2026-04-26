import { useState } from "react"

import { Download, Eye, History } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { useI18n } from "@/i18n/I18nProvider"

import { useHistoryQuery, downloadExport } from "../hooks/useReimbursementExports"
import type { ReimbursementExportPublic } from "../types"
import { ExportDetailDialog } from "./ExportDetailDialog"

export function HistoryTab() {
  const { t } = useI18n()
  const [filters, setFilters] = useState<{
    created_at_from?: string
    created_at_to?: string
    created_by_id?: string
    currency?: string
    skip?: number
    limit?: number
  }>({ limit: 100 })
  const [detailId, setDetailId] = useState<string | null>(null)

  const { data, isLoading, error } = useHistoryQuery(filters)
  const history = data?.data ?? []
  const count = data?.count ?? 0

  const updateFilter = <K extends keyof typeof filters>(
    key: K,
    value: (typeof filters)[K],
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  const handleDownload = async (item: ReimbursementExportPublic) => {
    try {
      await downloadExport(
        item.id,
        item.original_filename ?? item.stored_filename ?? `export_${item.id}.xlsx`,
      )
    } catch (err) {
      if (err instanceof Error && err.message === "expired") {
        alert(t("finance.reimbursementExports.errors.fileExpired"))
      } else {
        alert(t("finance.reimbursementExports.errors.downloadFailed"))
      }
    }
  }

  const isDownloadable = (item: ReimbursementExportPublic) => {
    if (item.file_deleted_at) return false
    if (item.file_expires_at && new Date(item.file_expires_at) < new Date()) return false
    return true
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
          type="datetime-local"
          placeholder={t("finance.reimbursementExports.filters.createdAtFrom")}
          value={filters.created_at_from ?? ""}
          onChange={(e) =>
            updateFilter("created_at_from", e.target.value || undefined)
          }
        />
        <Input
          type="datetime-local"
          placeholder={t("finance.reimbursementExports.filters.createdAtTo")}
          value={filters.created_at_to ?? ""}
          onChange={(e) =>
            updateFilter("created_at_to", e.target.value || undefined)
          }
        />
        <Input
          placeholder={t("finance.reimbursementExports.filters.createdById")}
          className="w-48"
          value={filters.created_by_id ?? ""}
          onChange={(e) =>
            updateFilter("created_by_id", e.target.value || undefined)
          }
        />
        <Input
          placeholder={t("finance.reimbursementExports.filters.currency")}
          className="w-24"
          value={filters.currency ?? ""}
          onChange={(e) =>
            updateFilter("currency", e.target.value || undefined)
          }
        />
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : history.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="mb-4 rounded-full bg-muted p-4">
            <History className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold">
            {t("finance.reimbursementExports.empty.historyTitle")}
          </h3>
          <p className="text-muted-foreground">
            {t("finance.reimbursementExports.empty.historyDescription")}
          </p>
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("finance.reimbursementExports.columns.createdAt")}</TableHead>
                <TableHead>{t("finance.reimbursementExports.columns.department")}</TableHead>
                <TableHead>{t("finance.reimbursementExports.columns.reimburser")}</TableHead>
                <TableHead>{t("finance.reimbursementExports.columns.itemCount")}</TableHead>
                <TableHead>{t("finance.reimbursementExports.columns.currency")}</TableHead>
                <TableHead>{t("finance.reimbursementExports.columns.totalAmount")}</TableHead>
                <TableHead>{t("finance.reimbursementExports.columns.fileStatus")}</TableHead>
                <TableHead className="text-right">
                  {t("finance.reimbursementExports.columns.actions")}
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {history.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{new Date(item.created_at).toLocaleString()}</TableCell>
                  <TableCell>{item.department ?? "—"}</TableCell>
                  <TableCell>{item.reimburser ?? "—"}</TableCell>
                  <TableCell>{item.item_count}</TableCell>
                  <TableCell>{item.currency ?? "—"}</TableCell>
                  <TableCell>{item.total_amount}</TableCell>
                  <TableCell>
                    {item.file_deleted_at ? (
                      <Badge variant="destructive">
                        {t("finance.reimbursementExports.status.purged")}
                      </Badge>
                    ) : item.file_expires_at &&
                      new Date(item.file_expires_at) < new Date() ? (
                      <Badge variant="secondary">
                        {t("finance.reimbursementExports.status.expired")}
                      </Badge>
                    ) : (
                      <Badge variant="default">
                        {t("finance.reimbursementExports.status.available")}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="flex justify-end gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setDetailId(item.id)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={!isDownloadable(item)}
                      onClick={() => handleDownload(item)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <div className="text-muted-foreground text-sm">
        {t("finance.reimbursementExports.records.total").replace("{count}", String(count))}
      </div>

      <ExportDetailDialog
        exportId={detailId}
        onClose={() => setDetailId(null)}
      />
    </div>
  )
}
