import { useQuery } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { getSystemDashboardStats } from "../api"

const TYPE_LABELS: Record<string, string> = {
  SINGLE_CHOICE: "单选题",
  MULTIPLE_CHOICE: "多选题",
  TRUE_FALSE: "判断题",
}

export function SystemDashboardPage() {
  const statsQuery = useQuery({
    queryKey: ["systemDashboardStats"],
    queryFn: getSystemDashboardStats,
  })

  const stats = statsQuery.data

  if (statsQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="text-center py-12 text-muted-foreground">暂无数据</div>
    )
  }

  const maxCount = Math.max(
    ...stats.question_type_distribution.map((d) => d.count),
    1,
  )

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">系统总览</h1>
        <p className="text-muted-foreground">考试系统累计数据统计</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>考试场数</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.exam_count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>总参与人次</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {stats.total_participation}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>及格率</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {stats.overall_pass_rate}%
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>题目总数</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.question_count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>试卷总数</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.paper_count}</div>
          </CardContent>
        </Card>
      </div>

      {/* Question type distribution bar chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">题库题型分布</CardTitle>
        </CardHeader>
        <CardContent>
          {stats.question_type_distribution.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              暂无题目数据
            </div>
          ) : (
            <div className="flex items-end gap-6 h-64">
              {stats.question_type_distribution.map((item) => (
                <div
                  key={item.question_type}
                  className="flex flex-col items-center gap-2 flex-1"
                >
                  <div className="text-sm font-medium">{item.count}</div>
                  <div
                    className="w-full bg-primary rounded-t-md transition-all"
                    style={{
                      height: `${(item.count / maxCount) * 200}px`,
                      minHeight: "4px",
                    }}
                  />
                  <div className="text-sm text-muted-foreground">
                    {TYPE_LABELS[item.question_type] || item.question_type}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
