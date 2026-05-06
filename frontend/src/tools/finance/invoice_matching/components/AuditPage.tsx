import { Eye, Inbox } from "lucide-react"
import { useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useI18n } from "@/i18n/I18nProvider"

import {
  useAllMatchesForAuditQuery,
  useApproveMatchMutation,
  useUnapproveMatchMutation,
} from "../hooks/useInvoiceMatching"
import type { InvoiceMatchPublic } from "../types"

import { MatchDetailDialog } from "./MatchList"

type AuditTab = "confirmed" | "approved"

function statusVariant(
  status: InvoiceMatchPublic["status"],
): "default" | "secondary" | "destructive" | "outline" {
  if (status === "approved") return "default"
  if (status === "confirmed") return "secondary"
  return "outline"
}

export function AuditPage() {
  const { t } = useI18n()
  const [tab, setTab] = useState<AuditTab>("confirmed")
  const [detailMatch, setDetailMatch] = useState<InvoiceMatchPublic | null>(null)

  const confirmedQuery = useAllMatchesForAuditQuery("confirmed")
  const approvedQuery = useAllMatchesForAuditQuery("approved")

  const approveMutation = useApproveMatchMutation()
  const unapproveMutation = useUnapproveMatchMutation()

  const data =
    tab === "confirmed"
      ? confirmedQuery.data?.data ?? []
      : approvedQuery.data?.data ?? []
  const isLoading =
    tab === "confirmed" ? confirmedQuery.isLoading : approvedQuery.isLoading

  const totalConfirmed = confirmedQuery.data?.count ?? 0
  const totalApproved = approvedQuery.data?.count ?? 0

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {t("finance.invoiceMatching.auditTitle")}
        </h1>
        <p className="text-muted-foreground">
          {t("finance.invoiceMatching.auditSubtitle")}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-2">
        <Card data-testid="audit-summary-confirmed">
          <CardHeader className="px-4">
            <CardDescription>
              {t("finance.invoiceMatching.summary.pendingAudit")}
            </CardDescription>
            <CardTitle className="text-2xl">{totalConfirmed}</CardTitle>
          </CardHeader>
        </Card>
        <Card data-testid="audit-summary-approved">
          <CardHeader className="px-4">
            <CardDescription>
              {t("finance.invoiceMatching.summary.approved")}
            </CardDescription>
            <CardTitle className="text-2xl">{totalApproved}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Tabs value={tab} onValueChange={(v) => setTab(v as AuditTab)}>
        <TabsList>
          <TabsTrigger value="confirmed">
            {t("finance.invoiceMatching.tabs.pendingAudit")}
          </TabsTrigger>
          <TabsTrigger value="approved">
            {t("finance.invoiceMatching.tabs.approved")}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="confirmed">
          <AuditTable
            data={data}
            isLoading={isLoading}
            action="approve"
            onAction={(id) => approveMutation.mutate(id)}
            actionPending={approveMutation.isPending}
            onDetail={setDetailMatch}
          />
        </TabsContent>
        <TabsContent value="approved">
          <AuditTable
            data={data}
            isLoading={isLoading}
            action="unapprove"
            onAction={(id) => unapproveMutation.mutate(id)}
            actionPending={unapproveMutation.isPending}
            onDetail={setDetailMatch}
          />
        </TabsContent>
      </Tabs>

      <MatchDetailDialog
        match={detailMatch}
        open={!!detailMatch}
        onClose={() => setDetailMatch(null)}
      />
    </div>
  )
}

interface AuditTableProps {
  data: InvoiceMatchPublic[]
  isLoading: boolean
  action: "approve" | "unapprove"
  onAction: (id: string) => void
  actionPending: boolean
  onDetail: (match: InvoiceMatchPublic) => void
}

function AuditTable({
  data,
  isLoading,
  action,
  onAction,
  actionPending,
  onDetail,
}: AuditTableProps) {
  const { t } = useI18n()

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
          {t("finance.invoiceMatching.empty.audit")}
        </p>
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{t("finance.invoiceMatching.fields.owner")}</TableHead>
          <TableHead>
            {t("finance.purchaseRecords.columns.orderName")}
          </TableHead>
          <TableHead>
            {t("finance.invoiceFiles.columns.invoiceNumber")}
          </TableHead>
          <TableHead>{t("finance.invoiceMatching.fields.amount")}</TableHead>
          <TableHead>{t("finance.invoiceMatching.fields.status")}</TableHead>
          <TableHead>{t("finance.invoiceMatching.scoreLabel")}</TableHead>
          <TableHead className="text-right">
            {t("finance.purchaseRecords.columns.actions")}
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((match) => (
          <TableRow key={match.id}>
            <TableCell className="font-medium text-xs text-muted-foreground">
              {match.owner_id.slice(0, 8)}
            </TableCell>
            <TableCell>
              <button
                className="text-primary hover:underline"
                onClick={() => onDetail(match)}
              >
                {match.purchase_record_name ||
                  t("finance.invoiceMatching.unknownOrder")}
              </button>
            </TableCell>
            <TableCell>
              <button
                className="text-primary hover:underline"
                onClick={() => onDetail(match)}
              >
                {match.invoice_file_number ||
                  t("finance.invoiceMatching.unknownInvoice")}
              </button>
            </TableCell>
            <TableCell>
              {match.purchase_amount || "-"} /{" "}
              {match.invoice_amount || "-"}
            </TableCell>
            <TableCell>
              <Badge variant={statusVariant(match.status)}>
                {t(`finance.invoiceMatching.status.${match.status}`)}
              </Badge>
            </TableCell>
            <TableCell>{match.score}</TableCell>
            <TableCell className="text-right">
              <div className="flex items-center justify-end gap-2">
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => onDetail(match)}
                  aria-label={t("finance.invoiceMatching.actions.viewDetail")}
                >
                  <Eye className="h-4 w-4" />
                </Button>
                <Button
                  variant={action === "approve" ? "default" : "outline"}
                  size="sm"
                  onClick={() => onAction(match.id)}
                  disabled={actionPending}
                >
                  {actionPending
                    ? t(
                        `finance.invoiceMatching.actions.${action}ing`,
                      )
                    : t(
                        `finance.invoiceMatching.actions.${action}`,
                      )}
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
