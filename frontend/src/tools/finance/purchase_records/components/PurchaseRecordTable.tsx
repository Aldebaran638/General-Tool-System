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
import { CATEGORIES, SUBCATEGORIES } from "../schemas"
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

interface PurchaseRecordTableProps {
  records: PurchaseRecord[]
  onEdit: (record: PurchaseRecord) => void
  showDeleted: boolean
}

function StatusBadge({ status }: { status: PurchaseRecord["status"] }) {
  const variants: Record<PurchaseRecord["status"], "default" | "secondary" | "destructive" | "outline"> = {
    draft: "secondary",
    submitted: "default",
    approved: "default",
    rejected: "destructive",
  }

  const labels: Record<PurchaseRecord["status"], string> = {
    draft: "草稿",
    submitted: "已提交",
    approved: "已批准",
    rejected: "已驳回",
  }

  return <Badge variant={variants[status]}>{labels[status]}</Badge>
}

function MatchStatusBadge({ status }: { status: PurchaseRecord["invoice_match_status"] }) {
  if (status === "matched") {
    return <Badge variant="outline">已匹配发票</Badge>
  }
  return <Badge variant="outline">未匹配发票</Badge>
}

function getCategoryLabel(value: string) {
  return CATEGORIES.find((c) => c.value === value)?.label || value
}

function getSubcategoryLabel(value: string | null) {
  if (!value) return "-"
  return SUBCATEGORIES.find((s) => s.value === value)?.label || value
}

export function PurchaseRecordTable({
  records,
  onEdit,
  showDeleted,
}: PurchaseRecordTableProps) {
  const { user } = useAuth()
  const isAdmin = user?.is_superuser ?? false

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
    rejectMutation.mutate({ id, data: { reason: "管理员驳回" } })
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
          <TableHead>订单名称</TableHead>
          <TableHead>日期</TableHead>
          <TableHead>金额</TableHead>
          <TableHead>大类</TableHead>
          <TableHead>状态</TableHead>
          <TableHead>匹配状态</TableHead>
          <TableHead>截图</TableHead>
          <TableHead className="text-right">操作</TableHead>
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
              <StatusBadge status={record.status} />
            </TableCell>
            <TableCell>
              <MatchStatusBadge status={record.invoice_match_status} />
            </TableCell>
            <TableCell>
              <ScreenshotDownloadButton id={record.id} />
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
                      编辑
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && (record.status === "draft" || record.status === "rejected") && (
                    <DropdownMenuItem onClick={() => handleSubmit(record.id)}>
                      <Send className="mr-2 h-4 w-4" />
                      提交
                    </DropdownMenuItem>
                  )}

                  {!showDeleted && record.status === "submitted" && (
                    <DropdownMenuItem onClick={() => handleWithdraw(record.id)}>
                      <Undo2 className="mr-2 h-4 w-4" />
                      撤回提交
                    </DropdownMenuItem>
                  )}

                  {isAdmin && !showDeleted && record.status === "submitted" && (
                    <>
                      <DropdownMenuItem onClick={() => handleApprove(record.id)}>
                        <Send className="mr-2 h-4 w-4" />
                        批准
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleReject(record.id)}>
                        <RotateCcw className="mr-2 h-4 w-4" />
                        驳回
                      </DropdownMenuItem>
                    </>
                  )}

                  {isAdmin && !showDeleted && record.status === "approved" && (
                    <DropdownMenuItem onClick={() => handleUnapprove(record.id)}>
                      <Undo2 className="mr-2 h-4 w-4" />
                      撤回批准
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

function ScreenshotDownloadButton({ id }: { id: string }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleClick = async () => {
    setError(null)
    // Open blank window immediately to avoid popup blocker
    const previewWindow = window.open("", "_blank")
    if (!previewWindow) {
      setError("浏览器拦截了弹窗，请允许弹窗后重试")
      return
    }

    setLoading(true)
    try {
      const blob = await downloadScreenshot(id)
      const url = URL.createObjectURL(blob)
      previewWindow.location.href = url
      // Clean up object URL after a delay
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (error) {
      previewWindow.close()
      setError("截图下载失败，请稍后重试")
      console.error("截图下载失败:", error)
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
        查看
      </button>
      {error && <span className="text-xs text-destructive mt-1">{error}</span>}
    </div>
  )
}
