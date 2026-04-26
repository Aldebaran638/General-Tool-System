import { ChevronDown, ChevronRight, Inbox } from "lucide-react"
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

import { useUnmatchedPurchaseRecordsQuery } from "../hooks/useInvoiceMatching"
import type { UnmatchedPurchaseRecord } from "../types"

import { CandidateList } from "./CandidateList"

interface UnmatchedListProps {
  isAdmin: boolean
}

function PurchaseRecordCard({
  record,
  isAdmin,
}: {
  record: UnmatchedPurchaseRecord
  isAdmin: boolean
}) {
  const { t } = useI18n()
  const [open, setOpen] = useState(false)

  return (
    <Card data-testid="unmatched-purchase-record">
      <CardHeader className="px-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-1 flex-col gap-1">
            <CardTitle className="text-base">
              {record.order_name || t("finance.invoiceMatching.unknownOrder")}
            </CardTitle>
            <CardDescription>
              {t("finance.invoiceMatching.fields.purchaseDate")}:{" "}
              {record.purchase_date || "-"}
              {" · "}
              {t("finance.invoiceMatching.fields.amount")}: {record.amount}{" "}
              {record.currency}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {t(`finance.invoiceMatching.purchaseStatus.${record.status}`)}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setOpen((v) => !v)}
              data-testid="toggle-candidates"
            >
              {open ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
              {open
                ? t("finance.invoiceMatching.actions.hideCandidates")
                : t("finance.invoiceMatching.actions.showCandidates")}
            </Button>
          </div>
        </div>
      </CardHeader>
      {open && (
        <CardContent className="px-6">
          <CandidateList purchaseRecord={record} isAdmin={isAdmin} />
        </CardContent>
      )}
    </Card>
  )
}

export function UnmatchedList({ isAdmin }: UnmatchedListProps) {
  const { t } = useI18n()
  const { data, isLoading } = useUnmatchedPurchaseRecordsQuery()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="border-primary h-8 w-8 animate-spin rounded-full border-4 border-t-transparent" />
      </div>
    )
  }

  const records = data?.data ?? []

  if (records.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="bg-muted mb-4 rounded-full p-4">
          <Inbox className="text-muted-foreground h-8 w-8" />
        </div>
        <h3 className="text-lg font-semibold">
          {t("finance.invoiceMatching.empty.unmatchedTitle")}
        </h3>
        <p className="text-muted-foreground">
          {t("finance.invoiceMatching.empty.unmatchedDescription")}
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {records.map((record) => (
        <PurchaseRecordCard
          key={record.id}
          record={record}
          isAdmin={isAdmin}
        />
      ))}
    </div>
  )
}
