import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { Suspense, useState } from "react"
import { useTranslation } from "react-i18next"
import { OkrService, UsersService } from "@/client"
import { Skeleton } from "@/components/ui/skeleton"
import i18n from "@/i18n"
import { DepartmentPanel } from "@/tools/okr/overview/department-board/DepartmentPanel"
import {
  ALL_DEPARTMENTS_ID,
  DepartmentTabs,
} from "@/tools/okr/overview/department-board/DepartmentTabs"

function getDepartmentStatsQueryOptions() {
  return {
    queryFn: () => OkrService.readOverviewDepartments(),
    queryKey: ["okr", "overview", "departments"],
  }
}

export const Route = createFileRoute("/_layout/okr/department-board")({
  component: DepartmentBoardPage,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (!user.is_superuser) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: `${i18n.t("okr.departmentBoardTitle", "部门项目管理")} - ${i18n.t("app.name")}`,
      },
    ],
  }),
})

function DepartmentBoardContent() {
  const { data } = useSuspenseQuery(getDepartmentStatsQueryOptions())
  const [selectedId, setSelectedId] = useState<string>(ALL_DEPARTMENTS_ID)
  const departments = data.data

  return (
    <div>
      <DepartmentTabs
        departments={departments}
        selectedId={selectedId}
        onSelect={setSelectedId}
      />
      <div
        role="tabpanel"
        className="rounded-b-lg border border-border bg-card p-6"
      >
        <div key={selectedId} className="animate-fade-in-up">
          <DepartmentPanel departments={departments} selectedId={selectedId} />
        </div>
      </div>
    </div>
  )
}

function DepartmentBoardPage() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-heading">
          {t("okr.departmentBoardTitle", "部门项目管理")}
        </h1>
        <p className="text-body text-muted-foreground">
          {t(
            "okr.departmentBoardDescription",
            "按部门查看 KR 进展与 Objective 分布",
          )}
        </p>
      </div>
      <Suspense fallback={<Skeleton className="h-72 w-full" />}>
        <DepartmentBoardContent />
      </Suspense>
    </div>
  )
}
