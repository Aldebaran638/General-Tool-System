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

import { useExportDetailQuery } from "../hooks/useReimbursementExports"

interface ExportDetailDialogProps {
  exportId: string | null
  onClose: () => void
}

export function ExportDetailDialog({
  exportId,
  onClose,
}: ExportDetailDialogProps) {
  const { t } = useI18n()
  const { data, isLoading } = useExportDetailQuery(exportId)

  return (
    <Dialog open={!!exportId} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {t("finance.reimbursementExports.detail.title")}
          </DialogTitle>
          <DialogDescription>
            {data
              ? t("finance.reimbursementExports.detail.description")
                  .replace("{count}", String(data.item_count))
                  .replace("{total}", data.total_amount)
              : ""}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        ) : data ? (
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">
                  {t("finance.reimbursementExports.columns.department")}:{" "}
                </span>
                {data.department ?? "—"}
              </div>
              <div>
                <span className="text-muted-foreground">
                  {t("finance.reimbursementExports.columns.businessUnit")}:{" "}
                </span>
                {data.business_unit ?? "—"}
              </div>
              <div>
                <span className="text-muted-foreground">
                  {t("finance.reimbursementExports.columns.reimburser")}:{" "}
                </span>
                {data.reimburser ?? "—"}
              </div>
              <div>
                <span className="text-muted-foreground">
                  {t("finance.reimbursementExports.columns.reimbursementDate")}:{" "}
                </span>
                {data.reimbursement_date ?? "—"}
              </div>
              <div>
                <span className="text-muted-foreground">
                  {t("finance.reimbursementExports.columns.currency")}:{" "}
                </span>
                {data.currency ?? "—"}
              </div>
              <div>
                <span className="text-muted-foreground">
                  {t("finance.reimbursementExports.columns.createdAt")}:{" "}
                </span>
                {new Date(data.created_at).toLocaleString()}
              </div>
            </div>

            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t("finance.reimbursementExports.columns.documentNumber")}</TableHead>
                    <TableHead>{t("finance.reimbursementExports.columns.purchaseDate")}</TableHead>
                    <TableHead>{t("finance.reimbursementExports.columns.orderName")}</TableHead>
                    <TableHead>{t("finance.reimbursementExports.columns.category")}</TableHead>
                    <TableHead>{t("finance.reimbursementExports.columns.amount")}</TableHead>
                    <TableHead>{t("finance.reimbursementExports.columns.currency")}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.items.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>{item.document_number}</TableCell>
                      <TableCell>{item.purchase_date}</TableCell>
                      <TableCell className="font-medium">{item.order_name}</TableCell>
                      <TableCell>
                        {t(`finance.purchaseRecords.category.${item.category}` as any) || item.category}
                      </TableCell>
                      <TableCell>{item.amount}</TableCell>
                      <TableCell>{item.currency}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}
