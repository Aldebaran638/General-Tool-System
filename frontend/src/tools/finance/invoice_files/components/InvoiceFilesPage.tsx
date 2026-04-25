import { Plus, FileText, Search } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"

import { InvoiceFileForm } from "./InvoiceFileForm"
import { InvoiceFileTable } from "./InvoiceFileTable"
import { useInvoiceFilesQuery } from "../hooks/useInvoiceFiles"

export function InvoiceFilesPage() {
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
          <h1 className="text-2xl font-bold tracking-tight">发票文件</h1>
          <p className="text-muted-foreground">管理和确认您的发票文件</p>
        </div>
        <Button onClick={() => setIsFormOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          新建发票
        </Button>
      </div>

      <Tabs
        value={showDeleted ? "deleted" : "normal"}
        onValueChange={(value) => setShowDeleted(value === "deleted")}
      >
        <TabsList>
          <TabsTrigger value="normal">正常记录</TabsTrigger>
          <TabsTrigger value="deleted">已删除记录</TabsTrigger>
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
              ? "没有已删除的发票"
              : "您还没有发票文件"}
          </h3>
          <p className="text-muted-foreground">
            {showDeleted
              ? "删除的发票将在这里显示 30 天"
              : "点击上方按钮创建新的发票文件"}
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
