import { AlertCircle, ChevronDown, ChevronUp } from "lucide-react"
import { useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { useI18n } from "@/i18n/I18nProvider"

import {
  useCandidatesQuery,
  useConfirmMatchMutation,
} from "../hooks/useInvoiceMatching"
import type {
  CandidateInvoice,
  MatchLevel,
  UnmatchedPurchaseRecord,
} from "../types"

interface CandidateListProps {
  purchaseRecord: UnmatchedPurchaseRecord
  isAdmin: boolean
}

function levelVariant(
  level: MatchLevel,
): "default" | "secondary" | "destructive" | "outline" {
  if (level === "strong") return "default"
  if (level === "weak") return "secondary"
  return "outline"
}

function CandidateRow({
  candidate,
  purchaseRecordId,
  isAdmin,
}: {
  candidate: CandidateInvoice
  purchaseRecordId: string
  isAdmin: boolean
}) {
  const { t } = useI18n()
  const [expanded, setExpanded] = useState(false)
  const confirmMutation = useConfirmMatchMutation()

  const handleConfirm = () => {
    confirmMutation.mutate({
      purchase_record_id: purchaseRecordId,
      invoice_file_id: candidate.invoice_file_id,
    })
  }

  return (
    <Card className="py-4" data-testid="candidate-row">
      <CardContent className="flex flex-col gap-2 px-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-1 flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium">
                {candidate.invoice_number ||
                  t("finance.invoiceMatching.unknownInvoice")}
              </span>
              <Badge variant={levelVariant(candidate.level)}>
                {t(`finance.invoiceMatching.level.${candidate.level}`)}
              </Badge>
              <Badge variant="outline">
                {t("finance.invoiceMatching.scoreLabel")}: {candidate.score}
              </Badge>
            </div>
            <div className="text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 text-sm">
              <span>
                {t("finance.invoiceMatching.fields.seller")}:{" "}
                {candidate.seller || "-"}
              </span>
              <span>
                {t("finance.invoiceMatching.fields.invoiceDate")}:{" "}
                {candidate.invoice_date || "-"}
              </span>
              <span>
                {t("finance.invoiceMatching.fields.invoiceAmount")}:{" "}
                {candidate.invoice_amount} {candidate.currency}
              </span>
            </div>
            <div className="text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 text-sm">
              <span>
                {t("finance.invoiceMatching.fields.allocatedAmount")}:{" "}
                {candidate.allocated_amount}
              </span>
              <span>
                {t("finance.invoiceMatching.fields.remainingAmount")}:{" "}
                {candidate.remaining_amount}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded((v) => !v)}
              aria-label={t("finance.invoiceMatching.actions.toggleBreakdown")}
            >
              {expanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
              {t("finance.invoiceMatching.actions.scoreBreakdown")}
            </Button>
            {!isAdmin && (
              <Button
                size="sm"
                onClick={handleConfirm}
                disabled={confirmMutation.isPending}
              >
                {confirmMutation.isPending
                  ? t("finance.invoiceMatching.actions.confirming")
                  : t("finance.invoiceMatching.actions.confirm")}
              </Button>
            )}
          </div>
        </div>
        {expanded && (
          <div className="bg-muted/40 rounded-md p-3">
            <div className="mb-2 text-sm font-medium">
              {t("finance.invoiceMatching.scoreBreakdownTitle")}
            </div>
            <ul className="text-muted-foreground space-y-1 text-sm">
              {Object.keys(candidate.score_breakdown).length === 0 && (
                <li>{t("finance.invoiceMatching.scoreBreakdownEmpty")}</li>
              )}
              {Object.entries(candidate.score_breakdown).map(([key, value]) => (
                <li key={key}>
                  <span className="font-medium">
                    {t(`finance.invoiceMatching.scoreCategory.${key}`)}
                  </span>
                  : +{value}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function CandidateList({ purchaseRecord, isAdmin }: CandidateListProps) {
  const { t } = useI18n()
  const { data, isLoading, error } = useCandidatesQuery(purchaseRecord.id)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-6">
        <div className="border-primary h-6 w-6 animate-spin rounded-full border-4 border-t-transparent" />
      </div>
    )
  }

  if (error) {
    const msg = (error as Error).message || ""
    return (
      <Card className="py-4">
        <CardHeader className="px-4">
          <CardTitle className="text-destructive flex items-center gap-2 text-base">
            <AlertCircle className="h-4 w-4" />
            {t("finance.invoiceMatching.candidateBlocked")}
          </CardTitle>
          <CardDescription>{msg}</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const candidates = data?.data ?? []

  if (candidates.length === 0) {
    return (
      <p className="text-muted-foreground py-4 text-sm">
        {t("finance.invoiceMatching.empty.candidates")}
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {candidates.map((c) => (
        <CandidateRow
          key={c.invoice_file_id}
          candidate={c}
          purchaseRecordId={purchaseRecord.id}
          isAdmin={isAdmin}
        />
      ))}
    </div>
  )
}
