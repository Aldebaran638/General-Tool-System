import { Plus, Receipt, Search } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useI18n } from "@/i18n"

import { PurchaseRecordForm } from "./PurchaseRecordForm"
import { PurchaseRecordTable } from "./PurchaseRecordTable"
import { usePurchaseRecordsQuery } from "../hooks/usePurchaseRecords"

export function PurchaseRecordsPage() {
  const { t } = useI18n()
  const [showDeleted, setShowDeleted] = useState(false)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState<
    import("../types").PurchaseRecord | null
  >(null)

  const { data, isLoading } = usePurchaseRecordsQuery(showDeleted)

  const handleEdit = (record: import("../types").PurchaseRecord) => {
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
            {t("finance.purchaseRecords.title")}
          </h1>
          <p className="text-muted-foreground">
            {t("finance.purchaseRecords.title")}
          </p>
        </div>
        <Button onClick={() => setIsFormOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          {t("finance.purchaseRecords.form.titleCreate")}
        </Button>
      </div>

      <Tabs
        value={showDeleted ? "deleted" : "normal"}
        onValueChange={(value) => setShowDeleted(value === "deleted")}
      >
        <TabsList>
          <TabsTrigger value="normal">
            {t("finance.purchaseRecords.title")}
          </TabsTrigger>
          <TabsTrigger value="deleted">
            {t("common.status")}
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
              <Receipt className="h-8 w-8 text-muted-foreground" />
            ) : (
              <Search className="h-8 w-8 text-muted-foreground" />
            )}
          </div>
          <h3 className="text-lg font-semibold">
            {showDeleted
              ? t("finance.purchaseRecords.title")
              : t("finance.purchaseRecords.title")}
          </h3>
          <p className="text-muted-foreground">
            {showDeleted
              ? t("finance.purchaseRecords.title")
              : t("finance.purchaseRecords.form.titleCreate")}
          </p>
        </div>
      ) : (
        <PurchaseRecordTable
          records={records}
          onEdit={handleEdit}
          showDeleted={showDeleted}
        />
      )}

      <PurchaseRecordForm
        open={isFormOpen}
        onClose={handleCloseForm}
        record={editingRecord}
      />
    </div>
  )
}
