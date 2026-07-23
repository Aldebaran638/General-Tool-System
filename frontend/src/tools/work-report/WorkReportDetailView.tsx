import { useQuery } from "@tanstack/react-query"
import { ArrowLeft, CalendarDays, ClipboardList, UserRound } from "lucide-react"

import { WorkReportsService } from "@/client"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const emptyValue = (value: string | null | undefined) => value || "—"

const WorkReportDetailView = ({ reportId }: { reportId: string }) => {
  const query = useQuery({
    queryKey: ["work-report-detail", reportId],
    queryFn: () => WorkReportsService.readWorkReport({ reportId }),
  })

  if (query.isLoading) {
    return (
      <p className="py-20 text-center text-muted-foreground">
        正在加载汇报详情…
      </p>
    )
  }
  if (query.isError || !query.data) {
    return (
      <Alert variant="destructive">
        <AlertTitle>无法读取汇报</AlertTitle>
        <AlertDescription>汇报不存在，或你没有查看权限。</AlertDescription>
      </Alert>
    )
  }
  const report = query.data

  return (
    <div className="space-y-6">
      <Button variant="ghost" onClick={() => window.history.back()}>
        <ArrowLeft />
        返回汇报列表
      </Button>

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2 text-2xl">
                <ClipboardList className="h-6 w-6 text-primary" />
                {report.title}
              </CardTitle>
              <p className="mt-2 text-sm text-muted-foreground">
                提交于 {new Date(report.submitted_at).toLocaleString()}
              </p>
            </div>
            <Badge variant="secondary" className="text-sm">
              {report.report_type === "weekly" ? "周报" : "月报"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <InfoItem
            icon={<UserRound />}
            label="汇报人"
            value={report.reporter.name || report.reporter.email}
          />
          <InfoItem
            icon={<CalendarDays />}
            label="汇报周期"
            value={`${report.period_start} 至 ${report.period_end}`}
          />
          <InfoItem label="工作计划" value={`${report.counts.work_plans} 条`} />
          <InfoItem
            label="任务总结 / 复盘"
            value={`${report.counts.task_summaries} / ${report.counts.work_reviews} 条`}
          />
          <div className="sm:col-span-2 lg:col-span-4">
            <p className="text-xs text-muted-foreground">备注</p>
            <p className="mt-1 whitespace-pre-wrap text-sm">
              {emptyValue(report.remarks)}
            </p>
          </div>
        </CardContent>
      </Card>

      <DetailSection title={`工作计划（${report.work_plans.length}）`}>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>计划内容</TableHead>
              <TableHead>计划完成时间</TableHead>
              <TableHead>预期成果</TableHead>
              <TableHead>所需支持</TableHead>
              <TableHead>备注</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {report.work_plans.map((item) => (
              <TableRow key={item.id}>
                <WrapCell>{emptyValue(item.plan_content)}</WrapCell>
                <TableCell>
                  {emptyValue(item.planned_completion_date)}
                </TableCell>
                <WrapCell>{emptyValue(item.expected_result)}</WrapCell>
                <WrapCell>{emptyValue(item.support_needed)}</WrapCell>
                <WrapCell>{emptyValue(item.remarks)}</WrapCell>
              </TableRow>
            ))}
            {report.work_plans.length === 0 ? (
              <EmptyDetailRow columns={5} />
            ) : null}
          </TableBody>
        </Table>
      </DetailSection>

      <DetailSection title={`任务总结（${report.task_summaries.length}）`}>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>工作目标</TableHead>
              <TableHead>完成时间</TableHead>
              <TableHead>进展情况</TableHead>
              <TableHead>当前进度</TableHead>
              <TableHead>未完成原因</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {report.task_summaries.map((item) => (
              <TableRow key={item.id}>
                <WrapCell>{emptyValue(item.work_goal)}</WrapCell>
                <TableCell>{emptyValue(item.completion_date)}</TableCell>
                <WrapCell>{emptyValue(item.progress_description)}</WrapCell>
                <TableCell>
                  {item.progress == null ? (
                    "—"
                  ) : (
                    <div className="flex min-w-36 items-center gap-2">
                      <Progress value={item.progress} className="h-2" />
                      <span>{item.progress}%</span>
                    </div>
                  )}
                </TableCell>
                <WrapCell>{emptyValue(item.incomplete_reason)}</WrapCell>
              </TableRow>
            ))}
            {report.task_summaries.length === 0 ? (
              <EmptyDetailRow columns={5} />
            ) : null}
          </TableBody>
        </Table>
      </DetailSection>

      <DetailSection title={`工作复盘（${report.work_reviews.length}）`}>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>复盘模块</TableHead>
              <TableHead>复盘内容</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {report.work_reviews.map((item) => (
              <TableRow key={item.id}>
                <WrapCell>{emptyValue(item.review_module)}</WrapCell>
                <WrapCell>{emptyValue(item.review_content)}</WrapCell>
              </TableRow>
            ))}
            {report.work_reviews.length === 0 ? (
              <EmptyDetailRow columns={2} />
            ) : null}
          </TableBody>
        </Table>
      </DetailSection>
    </div>
  )
}

const InfoItem = ({
  icon,
  label,
  value,
}: {
  icon?: React.ReactNode
  label: string
  value: string
}) => (
  <div>
    <p className="flex items-center gap-1 text-xs text-muted-foreground">
      {icon}
      {label}
    </p>
    <p className="mt-1 font-medium">{value}</p>
  </div>
)

const DetailSection = ({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) => (
  <Card>
    <CardHeader>
      <CardTitle>{title}</CardTitle>
    </CardHeader>
    <CardContent>{children}</CardContent>
  </Card>
)

const WrapCell = ({ children }: { children: React.ReactNode }) => (
  <TableCell className="max-w-80 whitespace-pre-wrap align-top">
    {children}
  </TableCell>
)

const EmptyDetailRow = ({ columns }: { columns: number }) => (
  <TableRow>
    <TableCell
      colSpan={columns}
      className="h-24 text-center text-muted-foreground"
    >
      暂无记录
    </TableCell>
  </TableRow>
)

export default WorkReportDetailView
