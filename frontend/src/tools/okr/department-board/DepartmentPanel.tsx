import { useTranslation } from "react-i18next"
import type { DepartmentStats } from "@/client"
import { Progress } from "@/components/ui/progress"
import { KrTable } from "@/tools/okr/kr-shared"
import { ALL_DEPARTMENTS_ID } from "./DepartmentTabs"

interface DepartmentPanelProps {
  departments: DepartmentStats[]
  selectedId: string
}

export function DepartmentPanel({
  departments,
  selectedId,
}: DepartmentPanelProps) {
  if (selectedId === ALL_DEPARTMENTS_ID) {
    return <AllDepartmentsOverview departments={departments} />
  }

  const stats = departments.find((entry) => entry.department.id === selectedId)
  if (!stats) {
    return null
  }
  return <SingleDepartment stats={stats} />
}

function AllDepartmentsOverview({
  departments,
}: {
  departments: DepartmentStats[]
}) {
  const { t } = useTranslation()

  if (departments.length === 0) {
    return (
      <p className="text-body text-muted-foreground">
        {t("okr.noDepartments", "暂无部门数据")}
      </p>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {departments.map((stats) => {
        const avg = Math.round(stats.avg_progress)
        return (
          <div
            key={stats.department.id}
            className="flex flex-col gap-3 rounded-lg border border-border bg-background p-4"
          >
            <h3 className="truncate text-subheading">
              {stats.department.name}
            </h3>
            <div className="grid grid-cols-3 gap-2">
              <MiniStat
                label={t("okr.memberCount", "成员数")}
                value={stats.member_count}
              />
              <MiniStat
                label={t("okr.krTotal", "KR 总数")}
                value={stats.kr_count}
              />
              <MiniStat
                label={t("okr.objectiveCount", "涉及 Objective")}
                value={stats.objective_count}
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-caption text-muted-foreground">
                {t("okr.avgProgress", "平均进度")}
              </span>
              <Progress value={avg} className="h-2 flex-1" />
              <span className="w-10 text-right text-body text-muted-foreground">
                {avg}%
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function SingleDepartment({ stats }: { stats: DepartmentStats }) {
  const { t } = useTranslation()
  const avg = Math.round(stats.avg_progress)

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label={t("okr.memberCount", "成员数")}
          value={stats.member_count}
        />
        <StatCard label={t("okr.krTotal", "KR 总数")} value={stats.kr_count} />
        <StatCard
          label={t("okr.objectiveCount", "涉及 Objective")}
          value={stats.objective_count}
        />
        <div className="flex flex-col justify-center gap-2 rounded-lg border border-border bg-background p-4">
          <span className="text-caption text-muted-foreground">
            {t("okr.avgProgress", "平均进度")}
          </span>
          <div className="flex items-center gap-2">
            <Progress value={avg} className="h-2 flex-1" />
            <span className="w-10 text-right text-body text-muted-foreground">
              {avg}%
            </span>
          </div>
        </div>
      </div>

      {stats.objectives.length === 0 ? (
        <p className="text-body text-muted-foreground">
          {t("okr.noKrs", "暂无 KR")}
        </p>
      ) : (
        stats.objectives.map((objective) => (
          <section key={objective.objective_id} className="flex flex-col gap-2">
            <h3 className="text-subheading">{objective.objective_title}</h3>
            <div className="overflow-x-auto rounded-lg border border-border bg-background">
              <KrTable krs={objective.krs} showAssignee />
            </div>
          </section>
        ))
      )}
    </div>
  )
}

function MiniStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="truncate text-caption text-muted-foreground">
        {label}
      </span>
      <span className="text-subheading">{value}</span>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col justify-center gap-1 rounded-lg border border-border bg-background p-4">
      <span className="text-caption text-muted-foreground">{label}</span>
      <span className="text-subheading">{value}</span>
    </div>
  )
}
