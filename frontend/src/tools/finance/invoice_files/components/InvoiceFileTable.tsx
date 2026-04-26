import {
  FileText,
  MoreHorizontal,
  Pencil,
  RotateCcw,
  CheckCircle,
  Undo2,
  Ban,
  Trash2,
  Loader2,
  AlertTriangle,
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

import type { InvoiceFile } from "../types"
import { createInvoiceFileSchemas } from "../schemas"
import {
  useDeleteInvoiceFileMutation,
  useRestoreInvoiceFileMutation,
  useConfirmInvoiceFileMutation,
  useWithdrawConfirmationMutation,
  useVoidInvoiceFileMutation,
  useRestoreDraftMutation,
} from "../hooks/useInvoiceFiles"
import { downloadPdf } from "../api"
import useAuth from "@/hooks/useAuth"
import { useState } from "react"
import { useI18n } from "@/i18n/I18nProvider"

interface InvoiceFileTableProps {
  records: InvoiceFile[]
  onEdit: (record: InvoiceFile) => void
  showDeleted: boolean
}

function StatusBadge({ status, t }: { status: InvoiceFile["status"]; t: (key: string) => string }) {
  const variants: Record<InvoiceFile["status"], "default" | "secondary" | "destructive" | "outline"> = {
    draft: "secondary",
    confirmed: "default",
    voided: "destructive",
  }

  const labels: Record<InvoiceFile["status"], string> = {
    draft: t("finance.invoiceFiles.status.draft"),
    confirmed: t("finance.invoiceFiles.status.confirmed"),
    voided: t("finance.invoiceFiles.status.voided"),
  }

  return <Badge variant={variants[status]}>{labels[status]}</Badge>
}

export function InvoiceFileTable({
  records,
  onEdit,
  showDeleted,
}: InvoiceFileTableProps) {
  const { t } = useI18n()
  const { INVOICE_TYPES } = createInvoiceFileSchemas(t)

  const getInvoiceTypeLabel = (value: string) => {
    return INVOICE_TYPES.find((type) => type.value === value)?.label || value
  }

  const confirmMutation = useConfirmInvoiceFileMutation()
  const withdrawMutation = useWithdrawConfirmationMutation()
  const voidMutation = useVoidInvoiceFileMutation()
  const restoreDraftMutation = useRestoreDraftMutation()
  const deleteMutation = useDeleteInvoiceFileMutation()
  const restoreMutation = useRestoreInvoiceFileMutation()

  const handleConfirm = (id: string) => {
    confirmMutation.mutate(id)
  }

  const handleWithdraw = (id: string) => {
    withdrawMutation.mutate(id)
  }

  const handleVoid = (id: string) => {
    voidMutation.mutate(id)
  }

  const handleRestoreDraft = (id: string) => {
    restoreDraftMutation.mutate(id)
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
          <TableHead>{t("finance.invoiceFiles.columns.invoiceNumber")}</TableHead>
          <TableHead>{t("finance.invoiceFiles.columns.date")}</TableHead>
          <TableHead>{t("finance.invoiceFiles.columns.amount")}</TableHead>
          <TableHead>{t("finance.invoiceFiles.columns.currency")}</TableHead>
          <TableHead>{t("finance.invoiceFiles.columns.buyer")}</TableHead>
          <TableHead>{t("finance.invoiceFiles.columns.seller")}</TableHead>
          <TableHead>{t("finance.invoiceFiles.columns.type")}</TableHead>
          <TableHead>{t("finance.invoiceFiles.columns.status")}</TableHead>
          <TableHead>{t("finance.invoiceFiles.columns.pdf")}</TableHead>
          <TableHead className="text-right">{t("finance.invoiceFiles.columns.actions")}</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {records.map((record) => (
          <TableRow key={record.id}>
            <TableCell className="font-medium">
              <div className="flex flex-col gap-1">
                <span>{record.invoice_number}</span>
                <DuplicateWarning record={record} t={t} />
              </div>
            </TableCell>
            <TableCell>{record.invoice_date}</TableCell>
            <TableCell>{record.invoice_amount}</TableCell>
            <TableCell>{record.currency}</TableCell>
            <TableCell>{record.buyer}</TableCell>
            <TableCell>{record.seller}</TableCell>
            <TableCell>{getInvoiceTypeLabel(record.invoice_type)}</TableCell>
            <TableCell>
              <StatusBadge status={record.status} t={t} />
            </TableCell>
            <TableCell>
              <PdfDownloadButton id={record.id} fileName={record.pdf_original_name} t={t} />
            </TableCell>
            <TableCell className="text-right">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon-sm">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {!showDeleted && record.status === "draft" && (
                    <DropdownMenuItem onClick={() => onEdit(record)}>
                      <Pencil className="mr-2 h-4 w-4" />
                      {t("finance.invoiceFiles.actions.edit")}
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && record.status === "draft" && (
                    <DropdownMenuItem onClick={() => handleConfirm(record.id)}>
                      <CheckCircle className="mr-2 h-4 w-4" />
                      {t("finance.invoiceFiles.actions.confirm")}
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && record.status === "confirmed" && (
                    <DropdownMenuItem onClick={() => handleWithdraw(record.id)}>
                      <Undo2 className="mr-2 h-4 w-4" />
                      {t("finance.invoiceFiles.actions.withdraw")}
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && record.status === "confirmed" && (
                    <DropdownMenuItem onClick={() => handleVoid(record.id)}>
                      <Ban className="mr-2 h-4 w-4" />
                      {t("finance.invoiceFiles.actions.void")}
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && record.status === "voided" && (
                    <DropdownMenuItem onClick={() => handleRestoreDraft(record.id)}>
                      <RotateCcw className="mr-2 h-4 w-4" />
                      {t("finance.invoiceFiles.actions.restoreDraft")}
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && (
                    <DropdownMenuItem
                      onClick={() => handleDelete(record.id)}
                      className="text-destructive"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      {t("finance.invoiceFiles.actions.delete")}
                    </DropdownMenuItem>
                  )}

                  {showDeleted && (
                    <DropdownMenuItem onClick={() => handleRestore(record.id)}>
                      <RotateCcw className="mr-2 h-4 w-4" />
                      {t("finance.invoiceFiles.actions.restore")}
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

function DuplicateWarning({ record, t }: { record: InvoiceFile; t: (key: string) => string }) {
  const { user } = useAuth()
  const isAdmin = user?.is_superuser ?? false

  if (isAdmin && record.duplicate_warning) {
    return (
      <div className="flex items-center gap-1 text-xs text-amber-600">
        <AlertTriangle className="h-3 w-3" />
        <span>{record.duplicate_warning}</span>
        {record.duplicate_invoice_owner_count !== null && record.duplicate_invoice_owner_count !== undefined && (
          <span>({record.duplicate_invoice_owner_count}{t("finance.invoiceFiles.duplicateUsers")})</span>
        )}
      </div>
    )
  }

  return null
}

function PdfDownloadButton({ id, fileName: _fileName, t }: { id: string; fileName?: string; t: (key: string) => string }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleClick = async () => {
    setError(null)
    const previewWindow = window.open("", "_blank")
    if (!previewWindow) {
      setError(t("finance.invoiceFiles.messages.popupBlocked"))
      return
    }

    setLoading(true)
    try {
      const blob = await downloadPdf(id)
      const url = URL.createObjectURL(blob)
      previewWindow.location.href = url
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (error) {
      previewWindow.close()
      setError(t("finance.invoiceFiles.messages.downloadFailed"))
      console.error(t("finance.invoiceFiles.messages.downloadFailed"), error)
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
          <FileText className="mr-1 h-4 w-4" />
        )}
        {t("finance.invoiceFiles.columns.view")}
      </button>
      {error && <span className="text-xs text-destructive mt-1">{error}</span>}
    </div>
  )
}
