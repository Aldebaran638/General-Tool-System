import {
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { Suspense } from "react"
import { useTranslation } from "react-i18next"

import { OkrService, UsersService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import useCustomToast from "@/hooks/useCustomToast"
import i18n from "@/i18n"
import AddDepartment from "@/tools/okr/departments/AddDepartment"
import { getColumns } from "@/tools/okr/departments/columns"
import PendingDepartments from "@/tools/okr/departments/PendingDepartments"
import { handleError } from "@/utils"

function getDepartmentsQueryOptions() {
  return {
    queryFn: () => OkrService.readDepartments(),
    queryKey: ["departments"],
  }
}

export const Route = createFileRoute("/_layout/okr/departments")({
  component: Departments,
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
        title: `${i18n.t("nav.departments")} - ${i18n.t("app.name")}`,
      },
    ],
  }),
})

function DepartmentsTableContent() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { data: departments } = useSuspenseQuery(getDepartmentsQueryOptions())

  const reorderMutation = useMutation({
    mutationFn: (ids: string[]) =>
      OkrService.reorderDepartments({ requestBody: { ids } }),
    onSuccess: () => {
      showSuccessToast(t("okr.department.reordered"))
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["departments"] })
    },
  })

  const moveDepartment = (index: number, direction: -1 | 1) => {
    const ids = departments.data.map((department) => department.id)
    const target = index + direction
    if (target < 0 || target >= ids.length) {
      return
    }
    const [moved] = ids.splice(index, 1)
    ids.splice(target, 0, moved)
    reorderMutation.mutate(ids)
  }

  const columns = getColumns(t, {
    onMoveUp: (index) => moveDepartment(index, -1),
    onMoveDown: (index) => moveDepartment(index, 1),
  })

  return <DataTable columns={columns} data={departments.data} />
}

function DepartmentsTable() {
  return (
    <Suspense fallback={<PendingDepartments />}>
      <DepartmentsTableContent />
    </Suspense>
  )
}

function Departments() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading">{t("okr.department.pageTitle")}</h1>
          <p className="text-body text-muted-foreground">
            {t("okr.department.pageDescription")}
          </p>
        </div>
        <AddDepartment />
      </div>
      <DepartmentsTable />
    </div>
  )
}
