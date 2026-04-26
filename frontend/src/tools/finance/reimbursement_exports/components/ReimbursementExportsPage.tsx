import { useState } from "react"

import { Settings } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useI18n } from "@/i18n/I18nProvider"

import { RecordsTab } from "./RecordsTab"
import { HistoryTab } from "./HistoryTab"
import { SettingsDialog } from "./SettingsDialog"

type TabValue = "records" | "history"

export function ReimbursementExportsPage() {
  const { t } = useI18n()
  const [tab, setTab] = useState<TabValue>("records")
  const [settingsOpen, setSettingsOpen] = useState(false)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {t("finance.reimbursementExports.title")}
          </h1>
          <p className="text-muted-foreground">
            {t("finance.reimbursementExports.subtitle")}
          </p>
        </div>
        <Button variant="outline" onClick={() => setSettingsOpen(true)}>
          <Settings className="mr-2 h-4 w-4" />
          {t("finance.reimbursementExports.settings.title")}
        </Button>
      </div>

      <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
        <TabsList>
          <TabsTrigger value="records">
            {t("finance.reimbursementExports.tabs.records")}
          </TabsTrigger>
          <TabsTrigger value="history">
            {t("finance.reimbursementExports.tabs.history")}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="records">
          <RecordsTab />
        </TabsContent>
        <TabsContent value="history">
          <HistoryTab />
        </TabsContent>
      </Tabs>

      <SettingsDialog open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  )
}
