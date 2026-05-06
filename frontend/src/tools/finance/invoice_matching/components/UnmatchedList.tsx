import { ChevronDown, ChevronRight, Inbox } from "lucide-react"
import { Fragment, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useI18n } from "@/i18n/I18nProvider"

import { useUnmatchedPurchaseRecordsQuery } from "../hooks/useInvoiceMatching"
import type { UnmatchedPurchaseRecord } from "../types"

import { CandidateList } from "./CandidateList"

export function UnmatchedList() {
  const { t } = useI18n()
  const { data, isLoading } = useUnmatchedPurchaseRecordsQuery()
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  const toggleExpanded = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

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
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              {t("finance.purchaseRecords.columns.orderName")}
            </TableHead>
            <TableHead>
              {t("finance.invoiceMatching.fields.purchaseDate")}
            </TableHead>
            <TableHead>
              {t("finance.invoiceMatching.fields.amount")}
            </TableHead>
            <TableHead>
              {t("finance.purchaseRecords.columns.currency")}
            </TableHead>
            <TableHead>
              {t("finance.purchaseRecords.columns.status")}
            </TableHead>
            <TableHead className="text-right">
              {t("finance.purchaseRecords.columns.actions")}
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {records.map((record: UnmatchedPurchaseRecord) => {
            const expanded = expandedIds.has(record.id)
            return (
              <Fragment key={record.id}>
                <TableRow data-testid="unmatched-purchase-record">
                  <TableCell className="font-medium">
                    {record.order_name ||
                      t("finance.invoiceMatching.unknownOrder")}
                  </TableCell>
                  <TableCell>{record.purchase_date || "-"}</TableCell>
                  <TableCell>{record.amount}</TableCell>
                  <TableCell>{record.currency}</TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {t(
                        `finance.invoiceMatching.purchaseStatus.${record.status}`,
                      )}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleExpanded(record.id)}
                      data-testid="toggle-candidates"
                    >
                      {expanded ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                      {expanded
                        ? t(
                            "finance.invoiceMatching.actions.hideCandidates",
                          )
                        : t(
                            "finance.invoiceMatching.actions.showCandidates",
                          )}
                    </Button>
                  </TableCell>
                </TableRow>
                {expanded && (
                  <TableRow>
                    <TableCell colSpan={6} className="bg-muted/30 p-4">
                      <CandidateList
                        purchaseRecord={record}
                        isAdmin={isAdmin}
                      />
                    </TableCell>
                  </TableRow>
                )}
              </Fragment>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}
