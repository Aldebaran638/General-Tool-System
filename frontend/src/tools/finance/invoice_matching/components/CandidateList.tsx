import { AlertCircle, ChevronDown, ChevronUp, Search } from "lucide-react"
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
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useI18n } from "@/i18n/I18nProvider"

import {
  useCandidatesQuery,
  useConfirmMatchMutation,
  useSearchAvailableInvoicesQuery,
} from "../hooks/useInvoiceMatching"
import type {
  CandidateInvoice,
  MatchLevel,
  SearchableInvoice,
  UnmatchedPurchaseRecord,
} from "../types"

interface CandidateListProps {
  purchaseRecord: UnmatchedPurchaseRecord
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
}: {
  candidate: CandidateInvoice
  purchaseRecordId: string
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
            <Button
              size="sm"
              onClick={handleConfirm}
              disabled={confirmMutation.isPending}
            >
              {confirmMutation.isPending
                ? t("finance.invoiceMatching.actions.confirming")
                : t("finance.invoiceMatching.actions.confirm")}
            </Button>
          </div>
        </div>
        {expanded && (
          <div className="bg-muted/40 rounded-md p-3">
            <div className="mb-2 text-sm font-medium">
              {t("finance.invoiceMatching.scoreBreakdownTitle")}
            </div>
            <ul className="text-muted-foreground space-y-1 text-sm">
              {Object.keys(candidate.score_breakdown).length === 0 ? (
                <li>{t("finance.invoiceMatching.scoreBreakdownEmpty")}</li>
              ) : (
                Object.entries(candidate.score_breakdown).map(([key, value]) => (
                <li key={key}>
                  <span className="font-medium">
                    {t(`finance.invoiceMatching.scoreCategory.${key}`)}
                  </span>
                  : +{value}
                </li>
              )))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function SearchResultRow({
  invoice,
  purchaseRecordId,
}: {
  invoice: SearchableInvoice
  purchaseRecordId: string
}) {
  const { t } = useI18n()
  const confirmMutation = useConfirmMatchMutation()

  const handleConfirm = () => {
    confirmMutation.mutate({
      purchase_record_id: purchaseRecordId,
      invoice_file_id: invoice.id,
    })
  }

  return (
    <Card className="py-4" data-testid="search-result-row">
      <CardContent className="flex flex-col gap-2 px-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-1 flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium">
                {invoice.invoice_number ||
                  t("finance.invoiceMatching.unknownInvoice")}
              </span>
            </div>
            <div className="text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 text-sm">
              <span>
                {t("finance.invoiceMatching.fields.seller")}:{" "}
                {invoice.seller || "-"}
              </span>
              <span>
                {t("finance.invoiceMatching.fields.invoiceDate")}:{" "}
                {invoice.invoice_date || "-"}
              </span>
              <span>
                {t("finance.invoiceMatching.fields.invoiceAmount")}:{" "}
                {invoice.invoice_amount} {invoice.currency}
              </span>
            </div>
            <div className="text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 text-sm">
              <span>
                {t("finance.invoiceMatching.fields.remainingAmount")}:{" "}
                {invoice.remaining_amount}
              </span>
            </div>
          </div>
          
            <Button
              size="sm"
              onClick={handleConfirm}
              disabled={confirmMutation.isPending}
            >
              {confirmMutation.isPending
                ? t("finance.invoiceMatching.actions.confirming")
                : t("finance.invoiceMatching.actions.confirm")}
            </Button>
          
        </div>
      </CardContent>
    </Card>
  )
}

export function CandidateList({ purchaseRecord }: CandidateListProps) {
  const { t } = useI18n()
  const [activeTab, setActiveTab] = useState<"recommend" | "search">("recommend")
  const [searchInput, setSearchInput] = useState("")
  const [committedSearch, setCommittedSearch] = useState("")

  const { data, isLoading, error } = useCandidatesQuery(purchaseRecord.id)
  const searchQuery = useSearchAvailableInvoicesQuery(
    purchaseRecord.id,
    committedSearch,
    activeTab === "search" && committedSearch.trim().length > 0,
  )

  const handleSearch = () => {
    setCommittedSearch(searchInput)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSearch()
    }
  }

  const renderRecommendContent = () => {
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
          />
        ))}
      </div>
    )
  }

  const renderSearchContent = () => {
    return (
      <div className="flex flex-col gap-3">
        <div className="flex gap-2">
          <Input
            placeholder={t("finance.invoiceMatching.searchPlaceholder")}
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1"
          />
          <Button
            variant="secondary"
            onClick={handleSearch}
            disabled={searchQuery.isFetching || searchInput.trim().length === 0}
          >
            {searchQuery.isFetching ? (
              <div className="border-primary h-4 w-4 animate-spin rounded-full border-2 border-t-transparent" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            {t("finance.invoiceMatching.actions.search")}
          </Button>
        </div>

        {searchQuery.isLoading && (
          <div className="flex items-center justify-center py-6">
            <div className="border-primary h-6 w-6 animate-spin rounded-full border-4 border-t-transparent" />
          </div>
        )}

        {searchQuery.error && (
          <Card className="py-4">
            <CardHeader className="px-4">
              <CardTitle className="text-destructive flex items-center gap-2 text-base">
                <AlertCircle className="h-4 w-4" />
                {t("finance.invoiceMatching.searchFailed")}
              </CardTitle>
              <CardDescription>
                {(searchQuery.error as Error).message || ""}
              </CardDescription>
            </CardHeader>
          </Card>
        )}

        {!searchQuery.isLoading &&
          !searchQuery.error &&
          committedSearch.trim().length > 0 && (
            <>
              {(() => {
                const results = searchQuery.data?.data ?? []
                if (results.length === 0) {
                  return (
                    <p className="text-muted-foreground py-4 text-sm">
                      {t("finance.invoiceMatching.empty.searchResults")}
                    </p>
                  )
                }
                return (
                  <div className="flex flex-col gap-2">
                    {results.map((inv) => (
                      <SearchResultRow
                        key={inv.id}
                        invoice={inv}
                        purchaseRecordId={purchaseRecord.id}
                      />
                    ))}
                  </div>
                )
              })()}
            </>
          )}
      </div>
    )
  }

  return (
    <Tabs
      value={activeTab}
      onValueChange={(v) => setActiveTab(v as "recommend" | "search")}
    >
      <TabsList className="mb-3">
        <TabsTrigger value="recommend">
          {t("finance.invoiceMatching.tabs.recommend")}
        </TabsTrigger>
        <TabsTrigger value="search">
          {t("finance.invoiceMatching.tabs.manualSearch")}
        </TabsTrigger>
      </TabsList>
      <TabsContent value="recommend">{renderRecommendContent()}</TabsContent>
      <TabsContent value="search">{renderSearchContent()}</TabsContent>
    </Tabs>
  )
}
