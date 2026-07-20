import { useSuspenseQuery } from "@tanstack/react-query"
import {
  createFileRoute,
  Outlet,
  redirect,
  useRouterState,
} from "@tanstack/react-router"
import { Plus } from "lucide-react"
import { Suspense } from "react"
import { useTranslation } from "react-i18next"

import { OkrService, UsersService } from "@/client"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import i18n from "@/i18n"
import ObjectiveCard from "@/tools/okr/overview/ObjectiveCard"
import ObjectiveForm from "@/tools/okr/overview/ObjectiveForm"

function getObjectivesQueryOptions() {
  return {
    queryFn: () => OkrService.readObjectives(),
    queryKey: ["objectives"],
  }
}

export const Route = createFileRoute("/_layout/okr")({
  component: OkrPage,
  beforeLoad: async ({ location }) => {
    // /okr/my 是本路由的子路由，对全员开放；仅 OKR 总览页要求超管
    if (location.pathname.replace(/\/+$/, "") !== "/okr") {
      return
    }
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
        title: `${i18n.t("okr.overview.title", "OKR 总览")} - ${i18n.t("app.name")}`,
      },
    ],
  }),
})

function ObjectiveListContent() {
  const { t } = useTranslation()
  const { data: objectives } = useSuspenseQuery(getObjectivesQueryOptions())

  if (objectives.data.length === 0) {
    return (
      <p className="py-12 text-center text-body text-muted-foreground">
        {t("okr.overview.empty", "暂无目标，点击右上角「新建目标」创建。")}
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      {objectives.data.map((objective) => (
        <ObjectiveCard key={objective.id} objective={objective} />
      ))}
    </div>
  )
}

function ObjectiveList() {
  return (
    <Suspense
      fallback={
        <div className="flex flex-col gap-4">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-24 w-full rounded-lg" />
          ))}
        </div>
      }
    >
      <ObjectiveListContent />
    </Suspense>
  )
}

function OkrOverview() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading">
            {t("okr.overview.title", "OKR 总览")}
          </h1>
          <p className="text-muted-foreground">
            {t("okr.overview.description", "查看和管理所有目标与关键结果")}
          </p>
        </div>
        <ObjectiveForm
          trigger={
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              {t("okr.overview.newObjective", "新建目标")}
            </Button>
          }
        />
      </div>
      <ObjectiveList />
    </div>
  )
}

function OkrPage() {
  // /okr/my 作为子路由嵌套在本路由下；命中子路由时只渲染 Outlet
  const isChildRoute = useRouterState({
    select: (s) => s.location.pathname.replace(/\/+$/, "") !== "/okr",
  })

  if (isChildRoute) {
    return <Outlet />
  }
  return <OkrOverview />
}
