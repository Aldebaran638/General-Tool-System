import { Inbox } from "lucide-react"

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
  useCancelMatchMutation,
  useMatchesQuery,
  useReconfirmMatchMutation,
} from "../hooks/useInvoiceMatching"
import type { InvoiceMatchPublic, MatchStatus } from "../types"

interface MatchListProps {
  status: MatchStatus
  isAdmin: boolean
}

function statusVariant(
  status: MatchStatus,
): "default" | "secondary" | "destructive" | "outline" {
  if (status === "confirmed") return "default"
  if (status === "needs_review") return "secondary"
  return "destructive"
}

function MatchCard({
  match,
  isAdmin,
}: {
  match: InvoiceMatchPublic
  isAdmin: boolean
}) {
  const { t } = useI18n()
  const cancelMutation = useCancelMatchMutation()
  const reconfirmMutation = useReconfirmMatchMutation()

  return (
    <Card data-testid="match-card">
      <CardHeader className="px-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-1 flex-col gap-1">
            <CardTitle className="text-base">
              {t("finance.invoiceMatching.fields.purchaseRecordId")}:{" "}
              <span className="text-muted-foreground font-mono text-sm">
                {match.purchase_record_id}
              </span>
            </CardTitle>
            <CardDescription>
              {t("finance.invoiceMatching.fields.invoiceFileId")}:{" "}
              <span className="font-mono">{match.invoice_file_id}</span>
            </CardDescription>
            <div className="text-muted-foreground flex flex-wrap items-center gap-2 text-sm">
              <Badge variant={statusVariant(match.status)}>
                {t(`finance.invoiceMatching.status.${match.status}`)}
              </Badge>
              <Badge variant="outline">
                {t("finance.invoiceMatching.scoreLabel")}: {match.score}
              </Badge>
              {match.review_reason && (
                <Badge variant="secondary">
                  {t("finance.invoiceMatching.fields.reviewReason")}:{" "}
                  {match.review_reason}
                </Badge>
              )}
            </div>
          </div>
          {!isAdmin && (
            <div className="flex items-center gap-2">
              {match.status === "needs_review" && (
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
              {match.status !== "cancelled" && (
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
          )}
        </div>
      </CardHeader>
      <CardContent className="px-6">
        <div className="text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 text-sm">
          <span>
            {t("finance.invoiceMatching.fields.createdAt")}: {match.created_at}
          </span>
          {match.confirmed_at && (
            <span>
              {t("finance.invoiceMatching.fields.confirmedAt")}:{" "}
              {match.confirmed_at}
            </span>
          )}
          {match.cancelled_at && (
            <span>
              {t("finance.invoiceMatching.fields.cancelledAt")}:{" "}
              {match.cancelled_at}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export function MatchList({ status, isAdmin }: MatchListProps) {
  const { t } = useI18n()
  const { data, isLoading } = useMatchesQuery(status)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="border-primary h-8 w-8 animate-spin rounded-full border-4 border-t-transparent" />
      </div>
    )
  }

  const matches = data?.data ?? []

  if (matches.length === 0) {
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
    <div className="flex flex-col gap-3">
      {matches.map((m) => (
        <MatchCard key={m.id} match={m} isAdmin={isAdmin} />
      ))}
    </div>
  )
}
