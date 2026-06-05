import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { Loader2, GraduationCap } from "lucide-react"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { getTrainerSummary, type TrainerSummaryItem } from "../api"

function formatDateTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function TrainerSummaryPage() {
  const summaryQuery = useQuery({
    queryKey: ["trainerSummary"],
    queryFn: getTrainerSummary,
  })

  const items = summaryQuery.data?.data ?? []

  if (summaryQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (summaryQuery.isError) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        加载失败，请稍后重试
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">培训讲师汇总</h1>
        <p className="text-muted-foreground">
          共 {summaryQuery.data?.count ?? 0} 条记录
        </p>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground border rounded-lg">
          <GraduationCap className="h-12 w-12 mx-auto mb-3 text-muted-foreground/50" />
          <p>暂无培训讲师数据</p>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>讲师</TableHead>
              <TableHead>中心</TableHead>
              <TableHead>课程名称</TableHead>
              <TableHead>考试时间</TableHead>
              <TableHead>培训人数</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item: TrainerSummaryItem) => (
              <TableRow key={`${item.trainer_id}-${item.exam_id}`}>
                <TableCell>{item.trainer_name}</TableCell>
                <TableCell>{item.center ?? "—"}</TableCell>
                <TableCell>
                  <Link
                    to="/exams/$examId"
                    params={{ examId: item.exam_id }}
                    className="text-primary hover:underline font-medium"
                  >
                    {item.exam_name}
                  </Link>
                </TableCell>
                <TableCell>{formatDateTime(item.start_at)}</TableCell>
                <TableCell>{item.participant_count}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
