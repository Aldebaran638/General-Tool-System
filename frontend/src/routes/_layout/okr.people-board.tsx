import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { Suspense } from "react"
import { useTranslation } from "react-i18next"
import { OkrService, UsersService } from "@/client"
import { Skeleton } from "@/components/ui/skeleton"
import i18n from "@/i18n"
import { PeopleBoard } from "@/tools/okr/people-board/PeopleBoard"

function getUserStatsQueryOptions() {
  return {
    queryFn: () => OkrService.readStatsByUser(),
    queryKey: ["okr", "stats", "by-user"],
  }
}

export const Route = createFileRoute("/_layout/okr/people-board")({
  component: PeopleBoardPage,
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
        title: `${i18n.t("okr.peopleBoardTitle", "人员项目管理")} - ${i18n.t("app.name")}`,
      },
    ],
  }),
})

function PeopleBoardContent() {
  const { data } = useSuspenseQuery(getUserStatsQueryOptions())

  return <PeopleBoard users={data.data} />
}

function PeopleBoardPage() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-heading">
          {t("okr.peopleBoardTitle", "人员项目管理")}
        </h1>
        <p className="text-body text-muted-foreground">
          {t("okr.peopleBoardDescription", "按成员查看 KR 承担情况与进展")}
        </p>
      </div>
      <Suspense fallback={<Skeleton className="h-72 w-full" />}>
        <PeopleBoardContent />
      </Suspense>
    </div>
  )
}
