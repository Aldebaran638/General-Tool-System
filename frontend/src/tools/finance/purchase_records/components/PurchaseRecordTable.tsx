import {
  FileImage,
  MoreHorizontal,
  Pencil,
  RotateCcw,
  Send,
  Trash2,
  Undo2,
  Loader2,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

import type { PurchaseRecord } from "../types"
import { createPurchaseRecordSchemas } from "../schemas"
import {
  useDeletePurchaseRecordMutation,
  useRestorePurchaseRecordMutation,
  useSubmitPurchaseRecordMutation,
  useWithdrawPurchaseRecordMutation,
  useApprovePurchaseRecordMutation,
  useRejectPurchaseRecordMutation,
  useUnapprovePurchaseRecordMutation,
} from "../hooks/usePurchaseRecords"
import { downloadScreenshot } from "../api"
import useAuth from "@/hooks/useAuth"
import { useState } from "react"
import { useI18n } from "@/i18n/I18nProvider"

interface PurchaseRecordTableProps {
  records: PurchaseRecord[]
  onEdit: (record: PurchaseRecord) => void
  showDeleted: boolean
}

function StatusBadge({ status, t }: { status: PurchaseRecord["status"]; t: (key: string) => string }) {
  const variants: Record<PurchaseRecord["status"], "default" | "secondary" | "destructive" | "outline"> = {
    draft: "secondary",
    submitted: "default",
    approved: "default",
    rejected: "destructive",
  }

  const labels: Record<PurchaseRecord["status"], string> = {
    draft: t("finance.purchaseRecords.status.draft"),
    submitted: t("finance.purchaseRecords.status.submitted"),
    approved: t("finance.purchaseRecords.status.approved"),
    rejected: t("finance.purchaseRecords.status.rejected"),
  }

  return <Badge variant={variants[status]}>{labels[status]}</Badge>
}

function MatchStatusBadge({ status, t }: { status: PurchaseRecord["invoice_match_status"]; t: (key: string) => string }) {
  if (status === "matched") {
    return <Badge variant="outline">{t("finance.purchaseRecords.invoiceMatchStatus.matched")}</Badge>
  }
  return <Badge variant="outline">{t("finance.purchaseRecords.invoiceMatchStatus.unmatched")}</Badge>
}

export function PurchaseRecordTable({
  records,
  onEdit,
  showDeleted,
}: PurchaseRecordTableProps) {
  const { user } = useAuth()
  const isAdmin = user?.is_superuser ?? false
  const { t } = useI18n()
  const { CATEGORIES, SUBCATEGORIES } = createPurchaseRecordSchemas(t)

  const getCategoryLabel = (value: string) => {
    return CATEGORIES.find((c) => c.value === value)?.label || value
  }

  const getSubcategoryLabel = (value: string | null) => {
    if (!value) return "-"
    return SUBCATEGORIES.find((s) => s.value === value)?.label || value
  }

  const submitMutation = useSubmitPurchaseRecordMutation()
  const withdrawMutation = useWithdrawPurchaseRecordMutation()
  const approveMutation = useApprovePurchaseRecordMutation()
  const rejectMutation = useRejectPurchaseRecordMutation()
  const unapproveMutation = useUnapprovePurchaseRecordMutation()
  const deleteMutation = useDeletePurchaseRecordMutation()
  const restoreMutation = useRestorePurchaseRecordMutation()

  const handleSubmit = (id: string) => {
    submitMutation.mutate(id)
  }

  const handleWithdraw = (id: string) => {
    withdrawMutation.mutate(id)
  }

  const handleApprove = (id: string) => {
    approveMutation.mutate(id)
  }

  const handleReject = (id: string) => {
    rejectMutation.mutate({ id, data: { reason: t("finance.purchaseRecords.messages.adminRejectReason") } })
  }

  const handleUnapprove = (id: string) => {
    unapproveMutation.mutate(id)
  }

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id)
  }

  const handleRestore = (id: string) => {
    restoreMutation.mutate(id)
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{t("finance.purchaseRecords.columns.orderName")}</TableHead>
          <TableHead>{t("finance.purchaseRecords.columns.date")}</TableHead>
          <TableHead>{t("finance.purchaseRecords.columns.amount")}</TableHead>
          <TableHead>{t("finance.purchaseRecords.columns.category")}</TableHead>
          <TableHead>{t("finance.purchaseRecords.columns.status")}</TableHead>
          <TableHead>{t("finance.purchaseRecords.columns.matchStatus")}</TableHead>
          <TableHead>{t("finance.purchaseRecords.columns.screenshot")}</TableHead>
          <TableHead className="text-right">{t("finance.purchaseRecords.columns.actions")}</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {records.map((record) => (
          <TableRow key={record.id}>
            <TableCell className="font-medium">{record.order_name}</TableCell>
            <TableCell>{record.purchase_date}</TableCell>
            <TableCell>
              {record.amount} {record.currency}
            </TableCell>
            <TableCell>
              {getCategoryLabel(record.category)}
              {record.subcategory && (
                <span className="ml-1 text-muted-foreground">
                  ({getSubcategoryLabel(record.subcategory)})
                </span>
              )}
            </TableCell>
            <TableCell>
              <StatusBadge status={record.status} t={t} />
            </TableCell>
            <TableCell>
              <MatchStatusBadge status={record.invoice_match_status} t={t} />
            </TableCell>
            <TableCell>
              <ScreenshotDownloadButton id={record.id} t={t} />
            </TableCell>
            <TableCell className="text-right">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon-sm">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {!showDeleted && (record.status === "draft" || record.status === "rejected") && (
                    <DropdownMenuItem onClick={() => onEdit(record)}>
                      <Pencil className="mr-2 h-4 w-4" />
                      {t("finance.purchaseRecords.actions.edit")}
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && (record.status === "draft" || record.status === "rejected") && (
                    <DropdownMenuItem onClick={() => handleSubmit(record.id)}>
                      <Send className="mr-2 h-4 w-4" />
                      {t("finance.purchaseRecords.actions.submit")}
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && record.status === "submitted" && (
                    <DropdownMenuItem onClick={() => handleWithdraw(record.id)}>
                      <Undo2 className="mr-2 h-4 w-4" />
                      {t("finance.purchaseRecords.actions.withdrawSubmit")}
                    </DropdownMenuItem>
                  )}

                  {isAdmin && !showDeleted && record.status === "submitted" && (
                    <>
                      <DropdownMenuItem onClick={() => handleApprove(record.id)}>
                        <Send className="mr-2 h-4 w-4" />
                        {t("finance.purchaseRecords.actions.approve")}
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleReject(record.id)}>
                        <RotateCcw className="mr-2 h-4 w-4" />
                        {t("finance.purchaseRecords.actions.reject")}
                      </DropdownMenuItem>
                    </>
                  )}

                  {isAdmin && !showDeleted && record.status === "approved" && (
                    <DropdownMenuItem onClick={() => handleUnapprove(record.id)}>
                      <Undo2 className="mr-2 h-4 w-4" />
                      {t("finance.purchaseRecords.actions.unapprove")}
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && (
                    <DropdownMenuItem
                      onClick={() => handleDelete(record.id)}
                      className="text-destructive"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      {t("finance.purchaseRecords.actions.delete")}
                    </DropdownMenuItem>
                  )}

                  {showDeleted && (
                    <DropdownMenuItem onClick={() => handleRestore(record.id)}>
                      <RotateCcw className="mr-2 h-4 w-4" />
                      {t("finance.purchaseRecords.actions.restore")}
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

function ScreenshotDownloadButton({ id, t }: { id: string; t: (key: string) => string }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleClick = async () => {
    setError(null)
    const previewWindow = window.open("", "_blank")
    if (!previewWindow) {
      setError(t("finance.purchaseRecords.messages.popupBlocked"))
      return
    }

    setLoading(true)
    try {
      const blob = await downloadScreenshot(id)
      const url = URL.createObjectURL(blob)
      previewWindow.location.href = url
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (error) {
      previewWindow.close()
      setError(t("finance.purchaseRecords.messages.downloadFailed"))
      console.error(t("finance.purchaseRecords.messages.downloadFailed"), error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="inline-flex flex-col items-start">
      <button
        onClick={handleClick}
        disabled={loading}
        className="inline-flex items-center text-primary hover:underline disabled:opacity-50"
      >
        {loading ? (
          <Loader2 className="mr-1 h-4 w-4 animate-spin" />
        ) : (
          <FileImage className="mr-1 h-4 w-4" />
        )}
        {t("finance.purchaseRecords.columns.view")}
      </button>
      {error && <span className="text-xs text-destructive mt-1">{error}</span>}
    </div>
  )
}
