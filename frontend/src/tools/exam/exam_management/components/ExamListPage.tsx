import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import {
  Plus,
  Search,
  MoreHorizontal,
  FileText,
  Archive,
  Trash2,
  Send,
  Loader2,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

import { listExams, deleteExam, publishExam, archiveExam } from "../api"
import type { Exam } from "../types"

function fmtDate(s: string | null): string {
  if (!s) return "—"
  return new Date(s).toLocaleString("zh-CN", { hour12: false })
}

function ExamStatusBadge({ exam }: { exam: Exam }) {
  const now = new Date()
  const start = new Date(exam.start_at)
  const end = new Date(exam.end_at)

  if (exam.status === "DRAFT")
    return <Badge variant="secondary">未发布</Badge>
  if (exam.status === "ARCHIVED")
    return <Badge variant="outline" className="text-muted-foreground">已归档</Badge>
  if (now < start)
    return <Badge variant="info">未开始</Badge>
  if (now > end)
    return <Badge variant="warning">已结束</Badge>
  return <Badge variant="success">进行中</Badge>
}

export function ExamListPage() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [search, setSearch] = useState("")
  const [deleteTarget, setDeleteTarget] = useState<Exam | null>(null)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const examsQuery = useQuery({
    queryKey: ["exams", page, statusFilter, search],
    queryFn: () =>
      listExams({
        page,
        status: statusFilter === "all" ? undefined : statusFilter,
        q: search || undefined,
      }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteExam(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exams"] })
      setDeleteTarget(null)
    },
  })

  const publishMutation = useMutation({
    mutationFn: (id: string) => publishExam(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["exams"] }),
  })

  const archiveMutation = useMutation({
    mutationFn: (id: string) => archiveExam(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["exams"] }),
  })

  const exams = examsQuery.data?.data ?? []
  const total = examsQuery.data?.count ?? 0
  const pageSize = 20
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">考试管理</h1>
          <p className="text-muted-foreground">创建和管理考试、编辑试卷、分配学员</p>
        </div>
        <Button onClick={() => navigate({ to: "/exams/new" })}>
          <Plus className="mr-2 h-4 w-4" />
          新建考试
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索考试名称…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="pl-8"
          />
        </div>
        <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1) }}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="考试状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部状态</SelectItem>
            <SelectItem value="DRAFT">未发布</SelectItem>
            <SelectItem value="PUBLISHED">已发布</SelectItem>
            <SelectItem value="ARCHIVED">已归档</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>考试名称</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>考试时间</TableHead>
              <TableHead className="text-right">时长(分)</TableHead>
              <TableHead className="text-right">及格分</TableHead>
              <TableHead>创建时间</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {examsQuery.isLoading && (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground">
                  <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />加载中…
                </TableCell>
              </TableRow>
            )}
            {!examsQuery.isLoading && exams.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-12">
                  <div className="flex flex-col items-center gap-3">
                    <div className="rounded-full bg-muted p-4">
                      <FileText className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="font-medium text-foreground">暂无考试</p>
                      <p className="text-sm text-muted-foreground mt-1">点击"新建考试"创建第一场考试</p>
                    </div>
                  </div>
                </TableCell>
              </TableRow>
            )}
            {exams.map((exam) => (
              <TableRow key={exam.id} className="group transition-colors hover:bg-muted/50">
                <TableCell className="font-medium">
                  <button
                    className="hover:underline text-left group-hover:text-primary transition-colors"
                    onClick={() => navigate({ to: `/exams/${exam.id}` })}
                  >
                    {exam.name}
                  </button>
                </TableCell>
                <TableCell>
                  <ExamStatusBadge exam={exam} />
                </TableCell>
                <TableCell className="text-sm whitespace-nowrap">
                  {fmtDate(exam.start_at)}
                  <br />
                  <span className="text-muted-foreground">~ {fmtDate(exam.end_at)}</span>
                </TableCell>
                <TableCell className="text-right">{exam.duration_minutes}</TableCell>
                <TableCell className="text-right">{exam.pass_score}</TableCell>
                <TableCell className="text-sm">{fmtDate(exam.created_at)}</TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={() => navigate({ to: `/exams/${exam.id}` })}
                      >
                        <FileText className="mr-2 h-4 w-4" />编辑
                      </DropdownMenuItem>
                      {exam.status === "DRAFT" && (
                        <DropdownMenuItem
                          onClick={() => publishMutation.mutate(exam.id)}
                          disabled={publishMutation.isPending}
                        >
                          <Send className="mr-2 h-4 w-4" />发布
                        </DropdownMenuItem>
                      )}
                      {exam.status === "PUBLISHED" && (
                        <DropdownMenuItem
                          onClick={() => archiveMutation.mutate(exam.id)}
                          disabled={archiveMutation.isPending}
                        >
                          <Archive className="mr-2 h-4 w-4" />归档
                        </DropdownMenuItem>
                      )}
                      {exam.status === "DRAFT" && (
                        <DropdownMenuItem
                          className="text-red-600"
                          onClick={() => setDeleteTarget(exam)}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />删除
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-end gap-2 text-sm">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            上一页
          </Button>
          <span className="text-muted-foreground">
            第 {page} / {totalPages} 页，共 {total} 条
          </span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
            下一页
          </Button>
        </div>
      )}

      {/* Delete confirmation dialog */}
      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              确定要删除考试"{deleteTarget?.name}"吗？此操作不可撤销。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>取消</Button>
            <Button
              variant="destructive"
              onClick={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
