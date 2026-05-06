import { FileImage, FileText, Inbox, Eye } from "lucide-react"
import { useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useI18n } from "@/i18n/I18nProvider"

import { downloadPdf } from "../../invoice_files/api"
import { downloadScreenshot } from "../../purchase_records/api"
import {
  useCancelMatchMutation,
  useMatchesQuery,
  useReconfirmMatchMutation,
} from "../hooks/useInvoiceMatching"
import type { InvoiceMatchPublic, MatchStatus } from "../types"

interface MatchListProps {
  status: MatchStatus
  includeNeedsReview?: boolean
}

const REVIEW_REASON_MAP: Record<string, string> = {
  "purchase record updated": "purchaseRecordUpdated",
  "purchase record withdrawn to draft": "purchaseRecordWithdrawnToDraft",
  "purchase record rejected": "purchaseRecordRejected",
  "purchase record deleted": "purchaseRecordDeleted",
  "purchase record restored": "purchaseRecordRestored",
  "invoice file updated": "invoiceFileUpdated",
  "invoice file withdrawn to draft": "invoiceFileWithdrawnToDraft",
  "invoice file voided": "invoiceFileVoided",
  "invoice file restored to draft": "invoiceFileRestoredToDraft",
  "invoice file deleted": "invoiceFileDeleted",
  "invoice file restored": "invoiceFileRestored",
}

function getReviewReasonKey(reason: string | null): string {
  if (!reason) return ""
  return REVIEW_REASON_MAP[reason] || reason
}

function statusVariant(
  status: MatchStatus,
): "default" | "secondary" | "destructive" | "outline" {
  if (status === "approved") return "default"
  if (status === "confirmed") return "default"
  if (status === "needs_review") return "secondary"
  return "destructive"
}

export function MatchDetailDialog({
  match,
  open,
  onClose,
}: {
  match: InvoiceMatchPublic | null
  open: boolean
  onClose: () => void
}) {
  const { t } = useI18n()
  const [previewLoading, setPreviewLoading] = useState<
    "screenshot" | "pdf" | null
  >(null)

  if (!match) return null

  const handlePreviewScreenshot = async () => {
    setPreviewLoading("screenshot")
    const previewWindow = window.open("", "_blank")
    if (!previewWindow) {
      setPreviewLoading(null)
      return
    }
    try {
      const blob = await downloadScreenshot(match.purchase_record_id)
      const url = URL.createObjectURL(blob)
      previewWindow.location.href = url
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch {
      previewWindow.close()
    } finally {
      setPreviewLoading(null)
    }
  }

  const handlePreviewPdf = async () => {
    setPreviewLoading("pdf")
    const previewWindow = window.open("", "_blank")
    if (!previewWindow) {
      setPreviewLoading(null)
      return
    }
    try {
      const blob = await downloadPdf(match.invoice_file_id)
      const url = URL.createObjectURL(blob)
      previewWindow.location.href = url
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch {
      previewWindow.close()
    } finally {
      setPreviewLoading(null)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("finance.invoiceMatching.detailTitle")}</DialogTitle>
          <DialogDescription>
            {t("finance.invoiceMatching.detailDescription")}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="rounded-lg border p-4">
            <div className="mb-2 flex items-center justify-between">
              <h4 className="font-semibold">
                {t("finance.purchaseRecords.title")}
              </h4>
              <Button
                variant="outline"
                size="sm"
                onClick={handlePreviewScreenshot}
                disabled={previewLoading === "screenshot"}
              >
                <FileImage className="mr-2 h-4 w-4" />
                {t("finance.invoiceMatching.actions.viewScreenshot")}
              </Button>
            </div>
            <div className="text-muted-foreground space-y-1 text-sm">
              <p>
                <span className="font-medium">{t("finance.purchaseRecords.columns.orderName")}:</span>{" "}
                {match.purchase_record_name || "-"}
              </p>
              <p>
                <span className="font-medium">{t("finance.invoiceMatching.fields.purchaseDate")}:</span>{" "}
                {match.purchase_date || "-"}
              </p>
              <p>
                <span className="font-medium">{t("finance.invoiceMatching.fields.amount")}:</span>{" "}
                {match.purchase_amount || "-"}
              </p>
            </div>
          </div>
          <div className="rounded-lg border p-4">
            <div className="mb-2 flex items-center justify-between">
              <h4 className="font-semibold">
                {t("finance.invoiceFiles.title")}
              </h4>
              <Button
                variant="outline"
                size="sm"
                onClick={handlePreviewPdf}
                disabled={previewLoading === "pdf"}
              >
                <FileText className="mr-2 h-4 w-4" />
                {t("finance.invoiceMatching.actions.viewPdf")}
              </Button>
            </div>
            <div className="text-muted-foreground space-y-1 text-sm">
              <p>
                <span className="font-medium">{t("finance.invoiceFiles.columns.invoiceNumber")}:</span>{" "}
                {match.invoice_file_number || "-"}
              </p>
              <p>
                <span className="font-medium">{t("finance.invoiceMatching.fields.seller")}:</span>{" "}
                {match.seller || "-"}
              </p>
              <p>
                <span className="font-medium">{t("finance.invoiceMatching.fields.invoiceDate")}:</span>{" "}
                {match.invoice_date || "-"}
              </p>
              <p>
                <span className="font-medium">{t("finance.invoiceMatching.fields.invoiceAmount")}:</span>{" "}
                {match.invoice_amount || "-"}
              </p>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function MatchList({ status, includeNeedsReview }: MatchListProps) {
  const { t } = useI18n()
  const confirmedQuery = useMatchesQuery("confirmed")
  const approvedQuery = useMatchesQuery("approved")
  const needsReviewQuery = useMatchesQuery("needs_review")
  const cancelledQuery = useMatchesQuery("cancelled")

  const cancelMutation = useCancelMatchMutation()
  const reconfirmMutation = useReconfirmMatchMutation()

  const [detailMatch, setDetailMatch] = useState<InvoiceMatchPublic | null>(null)

  let data: InvoiceMatchPublic[] = []
  let isLoading = false

  if (status === "confirmed") {
    data = confirmedQuery.data?.data ?? []
    isLoading = confirmedQuery.isLoading
    if (includeNeedsReview) {
      data = [
        ...data,
        ...(needsReviewQuery.data?.data ?? []),
      ].sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )
      isLoading = confirmedQuery.isLoading || needsReviewQuery.isLoading
    }
  } else if (status === "approved") {
    data = approvedQuery.data?.data ?? []
    isLoading = approvedQuery.isLoading
  } else if (status === "needs_review") {
    data = needsReviewQuery.data?.data ?? []
    isLoading = needsReviewQuery.isLoading
  } else if (status === "cancelled") {
    data = cancelledQuery.data?.data ?? []
    isLoading = cancelledQuery.isLoading
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="border-primary h-8 w-8 animate-spin rounded-full border-4 border-t-transparent" />
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="bg-muted mb-4 rounded-full p-4">
          <Inbox className="text-muted-foreground h-8 w-8" />
        </div>
        <p className="text-muted-foreground">
          {t(`finance.invoiceMatching.empty.${status}`)}
        </p>
      </div>
    )
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              {t("finance.purchaseRecords.columns.orderName")}
            </TableHead>
            <TableHead>
              {t("finance.invoiceFiles.columns.invoiceNumber")}
            </TableHead>
            <TableHead>{t("finance.invoiceMatching.fields.amount")}</TableHead>
            <TableHead>
              {t("finance.invoiceMatching.fields.currency")}
            </TableHead>
            <TableHead>{t("finance.invoiceMatching.fields.status")}</TableHead>
            <TableHead>{t("finance.invoiceMatching.scoreLabel")}</TableHead>
            <TableHead>
              {t("finance.invoiceMatching.fields.reviewReason")}
            </TableHead>
            <TableHead className="text-right">
              {t("finance.purchaseRecords.columns.actions")}
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((match) => {
            const reasonKey = getReviewReasonKey(match.review_reason)
            const reasonText = reasonKey
              ? t(`finance.invoiceMatching.reviewReasons.${reasonKey}`)
              : ""

            const canAct = match.status !== "cancelled" && match.status !== "approved"

            return (
              <TableRow key={match.id}>
                <TableCell className="font-medium">
                  <button
                    className="text-primary hover:underline"
                    onClick={() => setDetailMatch(match)}
                  >
                    {match.purchase_record_name ||
                      t("finance.invoiceMatching.unknownOrder")}
                  </button>
                </TableCell>
                <TableCell>
                  <button
                    className="text-primary hover:underline"
                    onClick={() => setDetailMatch(match)}
                  >
                    {match.invoice_file_number ||
                      t("finance.invoiceMatching.unknownInvoice")}
                  </button>
                </TableCell>
                <TableCell>
                  {match.purchase_amount || "-"} /{" "}
                  {match.invoice_amount || "-"}
                </TableCell>
                <TableCell>-</TableCell>
                <TableCell>
                  <Badge variant={statusVariant(match.status)}>
                    {t(`finance.invoiceMatching.status.${match.status}`)}
                  </Badge>
                </TableCell>
                <TableCell>{match.score}</TableCell>
                <TableCell className="max-w-[200px] truncate text-sm">
                  {reasonText || "-"}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => setDetailMatch(match)}
                      aria-label={t("finance.invoiceMatching.actions.viewDetail")}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    {canAct && match.status === "needs_review" && (
                      <Button
                        size="sm"
                        onClick={() => reconfirmMutation.mutate(match.id)}
                        disabled={reconfirmMutation.isPending}
                      >
                        {reconfirmMutation.isPending
                          ? t("finance.invoiceMatching.actions.reconfirming")
                          : t("finance.invoiceMatching.actions.reconfirm")}
                      </Button>
                    )}
                    {canAct && (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => cancelMutation.mutate(match.id)}
                        disabled={cancelMutation.isPending}
                      >
                        {cancelMutation.isPending
                          ? t("finance.invoiceMatching.actions.cancelling")
                          : t("finance.invoiceMatching.actions.cancel")}
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>

      <MatchDetailDialog
        match={detailMatch}
        open={!!detailMatch}
        onClose={() => setDetailMatch(null)}
      />
    </>
  )
}
