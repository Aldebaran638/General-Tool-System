import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { useTranslation } from "react-i18next"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import i18n from "@/i18n"
import MyKrList, { type MyKrFilter } from "@/tools/okr/my-tasks/MyKrList"

const FILTERS: Array<{
  value: MyKrFilter
  labelKey: string
  fallback: string
}> = [
  { value: "all", labelKey: "okr.my.filter.all", fallback: "全部" },
  { value: "active", labelKey: "okr.my.filter.active", fallback: "未到100%" },
  { value: "done", labelKey: "okr.my.filter.done", fallback: "已达100%" },
  {
    value: "due_soon",
    labelKey: "okr.my.filter.dueSoon",
    fallback: "即将到期",
  },
  { value: "overdue", labelKey: "okr.my.filter.overdue", fallback: "已超期" },
]

export const Route = createFileRoute("/_layout/okr/my")({
  component: MyTasks,
  head: () => ({
    meta: [
      {
        title: `${i18n.t("okr.my.title", "我的任务")} - ${i18n.t("app.name")}`,
      },
    ],
  }),
})

function MyTasks() {
  const { t } = useTranslation()
  const [filter, setFilter] = useState<MyKrFilter>("all")

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-heading">{t("okr.my.title", "我的任务")}</h1>
        <p className="text-muted-foreground">
          {t("okr.my.description", "查看分配给我的关键结果并更新进度")}
        </p>
      </div>

      <Tabs
        value={filter}
        onValueChange={(value) => setFilter(value as MyKrFilter)}
      >
        <TabsList>
          {FILTERS.map((f) => (
            <TabsTrigger key={f.value} value={f.value}>
              {t(f.labelKey, f.fallback)}
            </TabsTrigger>
          ))}
        </TabsList>
        <TabsContent value={filter} className="mt-4">
          <MyKrList filter={filter} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
