import { useState } from "react"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import useAuth from "@/hooks/useAuth"
import { useI18n } from "@/i18n/I18nProvider"

import { useMatchSummaryQuery } from "../hooks/useInvoiceMatching"

import { MatchList } from "./MatchList"
import { UnmatchedList } from "./UnmatchedList"

type TabValue = "unmatched" | "matched" | "needs_review" | "cancelled"

export function InvoiceMatchingPage() {
  const { t } = useI18n()
  const { user } = useAuth()
  const isAdmin = user?.is_superuser ?? false
  const [tab, setTab] = useState<TabValue>("unmatched")

  const { data: summary } = useMatchSummaryQuery()

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {t("finance.invoiceMatching.title")}
        </h1>
        <p className="text-muted-foreground">
          {t("finance.invoiceMatching.subtitle")}
        </p>
      </div>

      {summary && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          <Card data-testid="summary-confirmed">
            <CardHeader className="px-4">
              <CardDescription>
                {t("finance.invoiceMatching.summary.confirmed")}
              </CardDescription>
              <CardTitle className="text-2xl">
                {summary.total_confirmed}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card data-testid="summary-needs-review">
            <CardHeader className="px-4">
              <CardDescription>
                {t("finance.invoiceMatching.summary.needsReview")}
              </CardDescription>
              <CardTitle className="text-2xl">
                {summary.total_needs_review}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card data-testid="summary-cancelled">
            <CardHeader className="px-4">
              <CardDescription>
                {t("finance.invoiceMatching.summary.cancelled")}
              </CardDescription>
              <CardTitle className="text-2xl">
                {summary.total_cancelled}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card data-testid="summary-unmatched">
            <CardHeader className="px-4">
              <CardDescription>
                {t("finance.invoiceMatching.summary.unmatched")}
              </CardDescription>
              <CardTitle className="text-2xl">
                {summary.total_unmatched_purchase_records}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card data-testid="summary-available">
            <CardHeader className="px-4">
              <CardDescription>
                {t("finance.invoiceMatching.summary.availableInvoices")}
              </CardDescription>
              <CardTitle className="text-2xl">
                {summary.total_available_invoices}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
        <TabsList>
          <TabsTrigger value="unmatched">
            {t("finance.invoiceMatching.tabs.unmatched")}
          </TabsTrigger>
          <TabsTrigger value="matched">
            {t("finance.invoiceMatching.tabs.matched")}
          </TabsTrigger>
          <TabsTrigger value="needs_review">
            {t("finance.invoiceMatching.tabs.needsReview")}
          </TabsTrigger>
          <TabsTrigger value="cancelled">
            {t("finance.invoiceMatching.tabs.cancelled")}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="unmatched">
          <UnmatchedList isAdmin={isAdmin} />
        </TabsContent>
        <TabsContent value="matched">
          <MatchList status="confirmed" isAdmin={isAdmin} includeNeedsReview />
        </TabsContent>
        <TabsContent value="needs_review">
          <MatchList status="needs_review" isAdmin={isAdmin} />
        </TabsContent>
        <TabsContent value="cancelled">
          <MatchList status="cancelled" isAdmin={isAdmin} />
        </TabsContent>
      </Tabs>

      {isAdmin && (
        <Card>
          <CardContent className="text-muted-foreground px-6 py-4 text-sm">
            {t("finance.invoiceMatching.adminReadOnlyHint")}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
