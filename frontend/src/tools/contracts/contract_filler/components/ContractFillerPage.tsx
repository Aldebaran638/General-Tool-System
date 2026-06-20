import { useState } from "react"
import { Download, Save } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useI18n } from "@/i18n/I18nProvider"

import {
  useContractFieldsQuery,
  useContractPreviewQuery,
  useCreateVersionMutation,
  useExportVersionMutation,
  useUpdateVersionMutation,
} from "../hooks/useContractFiller"
import { downloadContractDocx } from "../api"
import type { FilledVersion } from "../types"
import { DocxPreview } from "./DocxPreview"
import { VersionNameDialog } from "./VersionNameDialog"
import { VersionsTab } from "./VersionsTab"

export function ContractFillerPage() {
  const { t } = useI18n()
  const [activeTab, setActiveTab] = useState("fill")
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({})
  const [currentVersionId, setCurrentVersionId] = useState<string | null>(null)
  const [saveDialogOpen, setSaveDialogOpen] = useState(false)
  const [exportDialogOpen, setExportDialogOpen] = useState(false)

  const { data: fields = [], isLoading: fieldsLoading } = useContractFieldsQuery()
  const { data: preview = [], isLoading: previewLoading } = useContractPreviewQuery()
  const createVersionMutation = useCreateVersionMutation()
  const updateVersionMutation = useUpdateVersionMutation()
  const exportVersionMutation = useExportVersionMutation()

  const handleFieldChange = (values: Record<string, string>) => {
    setFieldValues(values)
  }

  const handleSave = (name: string) => {
    if (currentVersionId) {
      updateVersionMutation.mutate({
        id: currentVersionId,
        data: {
          version_name: name,
          field_values: fieldValues,
        },
      })
    } else {
      createVersionMutation.mutate(
        {
          version_name: name,
          field_values: fieldValues,
        },
        {
          onSuccess: (version) => {
            setCurrentVersionId(version.id)
          },
        },
      )
    }
  }

  const handleExport = async (version: FilledVersion) => {
    const response = await exportVersionMutation.mutateAsync({
      id: version.id,
      request: {
        filename: `${version.version_name}.docx`,
      },
    })
    const blob = await downloadContractDocx(response.download_url)
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = response.filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const handleLoadVersion = (version: FilledVersion) => {
    setFieldValues(version.field_values)
    setCurrentVersionId(version.id)
    setActiveTab("fill")
  }

  const isLoading = fieldsLoading || previewLoading

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        加载中...
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {t("contracts.contractFiller.title")}
          </h1>
          <p className="text-muted-foreground">
            {t("contracts.contractFiller.description")}
          </p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="fill">填写合同</TabsTrigger>
          <TabsTrigger value="versions">保存的版本</TabsTrigger>
        </TabsList>

        <TabsContent value="fill" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>合同预览</CardTitle>
              <div className="flex gap-2">
                <Button onClick={() => setSaveDialogOpen(true)}>
                  <Save className="mr-2 h-4 w-4" />
                  {currentVersionId ? "更新版本" : "保存版本"}
                </Button>
                {currentVersionId && (
                  <Button
                    variant="outline"
                    onClick={() => setExportDialogOpen(true)}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    导出 DOCX
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <DocxPreview
                segments={preview}
                fields={fields}
                values={fieldValues}
                onChange={handleFieldChange}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="versions">
          <VersionsTab onLoad={handleLoadVersion} onExport={handleExport} />
        </TabsContent>
      </Tabs>

      <VersionNameDialog
        open={saveDialogOpen}
        onOpenChange={setSaveDialogOpen}
        onConfirm={handleSave}
      />

      {currentVersionId && (
        <VersionNameDialog
          open={exportDialogOpen}
          onOpenChange={setExportDialogOpen}
          onConfirm={async (name) => {
            const response = await exportVersionMutation.mutateAsync({
              id: currentVersionId,
              request: { filename: `${name}.docx` },
            })
            const blob = await downloadContractDocx(response.download_url)
            const url = URL.createObjectURL(blob)
            const link = document.createElement("a")
            link.href = url
            link.download = response.filename
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            URL.revokeObjectURL(url)
          }}
          title="导出 DOCX"
          description="输入导出文件的名称（不需要加 .docx 后缀）。"
          label="文件名称"
          placeholder="例如：张三合同2025"
          confirmText="导出"
        />
      )}
    </div>
  )
}
