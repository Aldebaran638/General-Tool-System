import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { Link as RouterLink } from "@tanstack/react-router"
import {
  ClipboardList,
  Filter,
  RotateCcw,
  Search,
  ShieldAlert,
} from "lucide-react"
import { type FormEvent, useState } from "react"

import {
  type ReportType,
  type WorkReportsReadAllWorkReportsData,
  type WorkReportsReadMyWorkReportsData,
  WorkReportsService,
} from "@/client"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import useAuth from "@/hooks/useAuth"

type FilterState = {
  reporter: string
  reportType: "" | ReportType
  periodFrom: string
  periodTo: string
  submittedFrom: string
  submittedTo: string
  keyword: string
}

const EMPTY_FILTERS: FilterState = {
  reporter: "",
  reportType: "",
  periodFrom: "",
  periodTo: "",
  submittedFrom: "",
  submittedTo: "",
  keyword: "",
}
const PAGE_SIZE = 20

const WorkReportHistory = ({ mode }: { mode: "mine" | "admin" }) => {
  const isAdminMode = mode === "admin"
  const { user } = useAuth()
  const [draft, setDraft] = useState<FilterState>(EMPTY_FILTERS)
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS)
  const [page, setPage] = useState(0)

  const query = useQuery({
    queryKey: ["work-report-history", mode, filters, page],
    queryFn: () => {
      const common: WorkReportsReadMyWorkReportsData = {
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
        reportType: filters.reportType || undefined,
        periodFrom: filters.periodFrom || undefined,
        periodTo: filters.periodTo || undefined,
        submittedFrom: filters.submittedFrom || undefined,
        submittedTo: filters.submittedTo || undefined,
        keyword: filters.keyword.trim() || undefined,
      }
      if (!isAdminMode) return WorkReportsService.readMyWorkReports(common)
      const adminFilters: WorkReportsReadAllWorkReportsData = {
        ...common,
        reporter: filters.reporter.trim() || undefined,
      }
      return WorkReportsService.readAllWorkReports(adminFilters)
    },
    enabled: !isAdminMode || Boolean(user?.is_superuser),
    placeholderData: keepPreviousData,
  })

  if (isAdminMode && user && !user.is_superuser) {
    return (
      <Alert variant="destructive">
        <ShieldAlert className="h-4 w-4" />
        <AlertTitle>无权访问</AlertTitle>
        <AlertDescription>仅超级管理员可以查看所有人的汇报。</AlertDescription>
      </Alert>
    )
  }

  const applyFilters = (event: FormEvent) => {
    event.preventDefault()
    setFilters(draft)
    setPage(0)
  }
  const resetFilters = () => {
    setDraft(EMPTY_FILTERS)
    setFilters(EMPTY_FILTERS)
    setPage(0)
  }
  const totalPages = Math.max(
    1,
    Math.ceil((query.data?.count ?? 0) / PAGE_SIZE),
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <ClipboardList className="h-6 w-6 text-primary" />
          {isAdminMode ? "全部工作汇报" : "我的工作汇报"}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {isAdminMode
            ? "按员工、类型、周期、提交日期或关键词筛选全部汇报。"
            : "查看并筛选自己提交过的工作汇报。"}
        </p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={applyFilters} className="grid gap-4 lg:grid-cols-4">
            {isAdminMode ? (
              <FilterField label="汇报人">
                <Input
                  value={draft.reporter}
                  onChange={(event) =>
                    setDraft({ ...draft, reporter: event.target.value })
                  }
                  placeholder="姓名或邮箱"
                />
              </FilterField>
            ) : null}
            <FilterField label="汇报类型">
              <select
                value={draft.reportType}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    reportType: event.target.value as FilterState["reportType"],
                  })
                }
                className="border-input bg-background h-9 w-full rounded-md border px-3 text-sm"
              >
                <option value="">全部类型</option>
                <option value="weekly">周报</option>
                <option value="monthly">月报</option>
              </select>
            </FilterField>
            <FilterField label="周期开始">
              <Input
                type="date"
                value={draft.periodFrom}
                onChange={(event) =>
                  setDraft({ ...draft, periodFrom: event.target.value })
                }
              />
            </FilterField>
            <FilterField label="周期结束">
              <Input
                type="date"
                value={draft.periodTo}
                onChange={(event) =>
                  setDraft({ ...draft, periodTo: event.target.value })
                }
              />
            </FilterField>
            <FilterField label="提交日期从">
              <Input
                type="date"
                value={draft.submittedFrom}
                onChange={(event) =>
                  setDraft({ ...draft, submittedFrom: event.target.value })
                }
              />
            </FilterField>
            <FilterField label="提交日期至">
              <Input
                type="date"
                value={draft.submittedTo}
                onChange={(event) =>
                  setDraft({ ...draft, submittedTo: event.target.value })
                }
              />
            </FilterField>
            <FilterField label="关键词">
              <Input
                value={draft.keyword}
                onChange={(event) =>
                  setDraft({ ...draft, keyword: event.target.value })
                }
                placeholder="标题或备注"
              />
            </FilterField>
            <div className="flex items-end gap-2">
              <Button type="submit">
                <Search />
                查询
              </Button>
              <Button type="button" variant="outline" onClick={resetFilters}>
                <RotateCcw />
                重置
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {query.isError ? (
        <Alert variant="destructive">
          <Filter className="h-4 w-4" />
          <AlertTitle>加载失败</AlertTitle>
          <AlertDescription>无法读取汇报历史，请稍后重试。</AlertDescription>
        </Alert>
      ) : null}

      <Table>
        <TableHeader>
          <TableRow>
            {isAdminMode ? <TableHead>汇报人</TableHead> : null}
            <TableHead>标题</TableHead>
            <TableHead>类型</TableHead>
            <TableHead>汇报周期</TableHead>
            <TableHead>计划 / 总结 / 复盘</TableHead>
            <TableHead>提交时间</TableHead>
            <TableHead className="text-right">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {query.data?.data.map((report) => (
            <TableRow key={report.id}>
              {isAdminMode ? (
                <TableCell>
                  {report.reporter.name || report.reporter.email}
                </TableCell>
              ) : null}
              <TableCell className="max-w-72 truncate font-medium">
                {report.title}
              </TableCell>
              <TableCell>
                <Badge variant="secondary">
                  {report.report_type === "weekly" ? "周报" : "月报"}
                </Badge>
              </TableCell>
              <TableCell>
                {report.period_start} 至 {report.period_end}
              </TableCell>
              <TableCell>
                {report.counts.work_plans} / {report.counts.task_summaries} /{" "}
                {report.counts.work_reviews}
              </TableCell>
              <TableCell>
                {new Date(report.submitted_at).toLocaleString()}
              </TableCell>
              <TableCell className="text-right">
                <Button asChild variant="outline" size="sm">
                  <RouterLink
                    to="/work-reports/$reportId"
                    params={{ reportId: report.id }}
                  >
                    查看详情
                  </RouterLink>
                </Button>
              </TableCell>
            </TableRow>
          ))}
          {!query.isLoading && query.data?.data.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={isAdminMode ? 7 : 6}
                className="h-32 text-center text-muted-foreground"
              >
                暂无符合条件的汇报
              </TableCell>
            </TableRow>
          ) : null}
          {query.isLoading ? (
            <TableRow>
              <TableCell
                colSpan={isAdminMode ? 7 : 6}
                className="h-32 text-center text-muted-foreground"
              >
                正在加载…
              </TableCell>
            </TableRow>
          ) : null}
        </TableBody>
      </Table>

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>共 {query.data?.count ?? 0} 条</span>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 0 || query.isFetching}
            onClick={() => setPage((value) => value - 1)}
          >
            上一页
          </Button>
          <span>
            第 {page + 1} / {totalPages} 页
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page + 1 >= totalPages || query.isFetching}
            onClick={() => setPage((value) => value + 1)}
          >
            下一页
          </Button>
        </div>
      </div>
    </div>
  )
}

const FilterField = ({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) => (
  <div className="space-y-2">
    <span className="text-sm font-medium">{label}</span>
    {children}
  </div>
)

export default WorkReportHistory
