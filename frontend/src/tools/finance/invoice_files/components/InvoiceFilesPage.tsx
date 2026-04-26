import { Plus, FileText, Search } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useI18n } from "@/i18n"

import { InvoiceFileForm } from "./InvoiceFileForm"
import { InvoiceFileTable } from "./InvoiceFileTable"
import { useInvoiceFilesQuery } from "../hooks/useInvoiceFiles"

export function InvoiceFilesPage() {
  const { t } = useI18n()
  const [showDeleted, setShowDeleted] = useState(false)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState<
    import("../types").InvoiceFile | null
  >(null)

  const { data, isLoading } = useInvoiceFilesQuery(showDeleted)

  const handleEdit = (record: import("../types").InvoiceFile) => {
    setEditingRecord(record)
    setIsFormOpen(true)
  }

  const handleCloseForm = () => {
    setIsFormOpen(false)
    setEditingRecord(null)
  }

  const records = data?.data || []

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {t("finance.invoiceFiles.title")}
          </h1>
          <p className="text-muted-foreground">
            {t("finance.invoiceFiles.title")}
          </p>
        </div>
        <Button onClick={() => setIsFormOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          {t("finance.invoiceFiles.form.titleCreate")}
        </Button>
      </div>

      <Tabs
        value={showDeleted ? "deleted" : "normal"}
        onValueChange={(value) => setShowDeleted(value === "deleted")}
      >
        <TabsList>
          <TabsTrigger value="normal">
            {t("finance.invoiceFiles.tabs.active")}
          </TabsTrigger>
          <TabsTrigger value="deleted">
            {t("finance.invoiceFiles.tabs.deleted")}
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : records.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="mb-4 rounded-full bg-muted p-4">
            {showDeleted ? (
              <FileText className="h-8 w-8 text-muted-foreground" />
            ) : (
              <Search className="h-8 w-8 text-muted-foreground" />
            )}
          </div>
          <h3 className="text-lg font-semibold">
            {showDeleted
              ? t("finance.invoiceFiles.tabs.deleted")
              : t("finance.invoiceFiles.title")}
          </h3>
          <p className="text-muted-foreground">
            {showDeleted
              ? t("finance.invoiceFiles.tabs.deleted")
              : t("finance.invoiceFiles.form.titleCreate")}
          </p>
        </div>
      ) : (
        <InvoiceFileTable
          records={records}
          onEdit={handleEdit}
          showDeleted={showDeleted}
        />
      )}

      <InvoiceFileForm
        open={isFormOpen}
        onClose={handleCloseForm}
        record={editingRecord}
      />
    </div>
  )
}
