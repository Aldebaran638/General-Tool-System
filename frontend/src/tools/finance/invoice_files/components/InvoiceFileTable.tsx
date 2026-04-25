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
import { INVOICE_TYPES } from "../schemas"
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

interface InvoiceFileTableProps {
  records: InvoiceFile[]
  onEdit: (record: InvoiceFile) => void
  showDeleted: boolean
}

function StatusBadge({ status }: { status: InvoiceFile["status"] }) {
  const variants: Record<InvoiceFile["status"], "default" | "secondary" | "destructive" | "outline"> = {
    draft: "secondary",
    confirmed: "default",
    voided: "destructive",
  }

  const labels: Record<InvoiceFile["status"], string> = {
    draft: "草稿",
    confirmed: "已确认",
    voided: "已作废",
  }

  return <Badge variant={variants[status]}>{labels[status]}</Badge>
}

function getInvoiceTypeLabel(value: string) {
  return INVOICE_TYPES.find((t) => t.value === value)?.label || value
}

function DuplicateWarning({ record }: { record: InvoiceFile }) {
  const { user } = useAuth()
  const isAdmin = user?.is_superuser ?? false

  if (isAdmin && record.duplicate_warning) {
    return (
      <div className="flex items-center gap-1 text-xs text-amber-600">
        <AlertTriangle className="h-3 w-3" />
        <span>{record.duplicate_warning}</span>
        {record.duplicate_invoice_owner_count !== null && record.duplicate_invoice_owner_count !== undefined && (
          <span>({record.duplicate_invoice_owner_count} 位用户)</span>
        )}
      </div>
    )
  }

  return null
}

export function InvoiceFileTable({
  records,
  onEdit,
  showDeleted,
}: InvoiceFileTableProps) {

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
          <TableHead>发票号码</TableHead>
          <TableHead>日期</TableHead>
          <TableHead>金额</TableHead>
          <TableHead>币种</TableHead>
          <TableHead>购买方</TableHead>
          <TableHead>销售方</TableHead>
          <TableHead>类型</TableHead>
          <TableHead>状态</TableHead>
          <TableHead>PDF</TableHead>
          <TableHead className="text-right">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {records.map((record) => (
          <TableRow key={record.id}>
            <TableCell className="font-medium">
              <div className="flex flex-col gap-1">
                <span>{record.invoice_number}</span>
                <DuplicateWarning record={record} />
              </div>
            </TableCell>
            <TableCell>{record.invoice_date}</TableCell>
            <TableCell>{record.invoice_amount}</TableCell>
            <TableCell>{record.currency}</TableCell>
            <TableCell>{record.buyer}</TableCell>
            <TableCell>{record.seller}</TableCell>
            <TableCell>{getInvoiceTypeLabel(record.invoice_type)}</TableCell>
            <TableCell>
              <StatusBadge status={record.status} />
            </TableCell>
            <TableCell>
              <PdfDownloadButton id={record.id} fileName={record.pdf_original_name} />
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
                      编辑
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && record.status === "draft" && (
                    <DropdownMenuItem onClick={() => handleConfirm(record.id)}>
                      <CheckCircle className="mr-2 h-4 w-4" />
                      确认
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && record.status === "confirmed" && (
                    <DropdownMenuItem onClick={() => handleWithdraw(record.id)}>
                      <Undo2 className="mr-2 h-4 w-4" />
                      撤回确认
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && record.status === "confirmed" && (
                    <DropdownMenuItem onClick={() => handleVoid(record.id)}>
                      <Ban className="mr-2 h-4 w-4" />
                      作废
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && record.status === "voided" && (
                    <DropdownMenuItem onClick={() => handleRestoreDraft(record.id)}>
                      <RotateCcw className="mr-2 h-4 w-4" />
                      恢复草稿
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && (
                    <DropdownMenuItem
                      onClick={() => handleDelete(record.id)}
                      className="text-destructive"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      删除
                    </DropdownMenuItem>
                  )}

                  {showDeleted && (
                    <DropdownMenuItem onClick={() => handleRestore(record.id)}>
                      <RotateCcw className="mr-2 h-4 w-4" />
                      恢复
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

function PdfDownloadButton({ id }: { id: string; fileName?: string }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleClick = async () => {
    setError(null)
    const previewWindow = window.open("", "_blank")
    if (!previewWindow) {
      setError("浏览器拦截了弹窗，请允许弹窗后重试")
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
      setError("PDF 下载失败，请稍后重试")
      console.error("PDF 下载失败:", error)
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
        查看
      </button>
      {error && <span className="text-xs text-destructive mt-1">{error}</span>}
    </div>
  )
}