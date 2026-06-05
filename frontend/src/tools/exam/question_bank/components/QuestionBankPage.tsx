/**
 * Question Bank Page — browse and download exam papers
 */

import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  Clock,
  Download,
  Eye,
  FileText,
  Search,
} from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import type { QuestionBankItem } from "../api"
import { downloadQuestionBank, listQuestionBank } from "../api"

function formatDate(s: string): string {
  return new Date(s).toLocaleString("zh-CN", { hour12: false })
}

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case "GENERATED":
      return (
        <Badge variant="success">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          已生成
        </Badge>
      )
    case "PENDING":
      return (
        <Badge variant="warning">
          <Clock className="mr-1 h-3 w-3" />
          生成中
        </Badge>
      )
    case "FAILED":
      return (
        <Badge variant="destructive">
          <AlertCircle className="mr-1 h-3 w-3" />
          生成失败
        </Badge>
      )
    default:
      return <Badge variant="outline">{status}</Badge>
  }
}

function QuestionBankCard({
  item,
  onPreview,
  onDownload,
}: {
  item: QuestionBankItem
  onPreview: (examId: string) => void
  onDownload: (examId: string) => void
}) {
  const isReady = item.status === "GENERATED"

  return (
    <Card className="group transition-shadow duration-200 hover:shadow-md">
      <CardContent className="flex items-center justify-between p-4 gap-4">
        <div className="flex items-center gap-4 flex-1 min-w-0">
          <div
            className={`rounded-lg p-2.5 flex-shrink-0 ${
              isReady
                ? "bg-primary/10 text-primary"
                : "bg-muted text-muted-foreground"
            }`}
          >
            <FileText className="h-5 w-5" />
          </div>
          <div className="flex flex-col gap-1 flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-medium truncate">{item.exam_name}</h3>
              {item.category_name && (
                <Badge variant="outline" className="flex-shrink-0">
                  {item.category_name}
                </Badge>
              )}
              <StatusBadge status={item.status} />
            </div>
            <div className="text-sm text-muted-foreground">
              {item.question_count} 题 · 总分 {item.total_score}
              {item.generated_at &&
                ` · 生成于 ${formatDate(item.generated_at)}`}
            </div>
          </div>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPreview(item.exam_id)}
            disabled={!isReady}
          >
            <Eye className="mr-2 h-4 w-4" />
            浏览
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onDownload(item.exam_id)}
            disabled={!isReady}
          >
            <Download className="mr-2 h-4 w-4" />
            下载
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function QuestionBankCardSkeleton() {
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-4">
        <div className="flex items-center gap-4 flex-1">
          <Skeleton className="h-10 w-10 rounded-lg" />
          <div className="flex flex-col gap-2 flex-1">
            <div className="flex items-center gap-2">
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-5 w-16" />
              <Skeleton className="h-5 w-16" />
            </div>
            <Skeleton className="h-4 w-64" />
          </div>
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-9 w-20" />
          <Skeleton className="h-9 w-20" />
        </div>
      </CardContent>
    </Card>
  )
}

export function QuestionBankPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")

  const bankQuery = useQuery({
    queryKey: ["questionBank", page],
    queryFn: () => listQuestionBank({ page, limit: 20 }),
  })

  const items = bankQuery.data?.data ?? []
  const total = bankQuery.data?.count ?? 0
  const pageSize = 20
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  // Client-side search filter
  const filteredItems = search
    ? items.filter((item) =>
        item.exam_name.toLowerCase().includes(search.toLowerCase()),
      )
    : items

  function handlePreview(examId: string) {
    navigate({ to: `/question-bank/${examId}` })
  }

  async function handleDownload(examId: string) {
    try {
      await downloadQuestionBank(examId)
    } catch (error) {
      toast.error("下载失败", {
        description: error instanceof Error ? error.message : "请稍后重试",
      })
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Page header */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-primary/10 p-2.5">
            <BookOpen className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">试题库</h1>
            <p className="text-muted-foreground">浏览和下载所有考试的试题</p>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="flex gap-4">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索考试名称..."
            className="pl-8"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Loading state */}
      {bankQuery.isLoading && (
        <div className="grid gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <QuestionBankCardSkeleton key={i} />
          ))}
        </div>
      )}

      {/* Error state */}
      {bankQuery.isError && (
        <Card className="border-destructive">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="rounded-full bg-destructive/10 p-4 mb-4">
              <AlertCircle className="h-12 w-12 text-destructive" />
            </div>
            <h3 className="text-lg font-semibold mb-1">加载失败</h3>
            <p className="text-muted-foreground text-center max-w-sm">
              {bankQuery.error?.message || "无法加载试题库，请稍后重试"}
            </p>
            <Button
              variant="outline"
              onClick={() => bankQuery.refetch()}
              className="mt-4"
            >
              重试
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {!bankQuery.isLoading && filteredItems.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-20">
            <div className="rounded-full bg-primary/10 p-5 mb-4">
              <BookOpen className="h-14 w-14 text-primary" />
            </div>
            <h3 className="text-lg font-semibold mb-2">
              {search ? "未找到匹配的试题" : "暂无试题文件"}
            </h3>
            <p className="text-muted-foreground text-center max-w-sm leading-relaxed">
              {search
                ? "请尝试其他搜索关键词"
                : "试题库中还没有已生成的试题文件，请等待管理员生成试题"}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Question bank list */}
      {!bankQuery.isLoading && filteredItems.length > 0 && (
        <div className="grid gap-4">
          {filteredItems.map((item) => (
            <QuestionBankCard
              key={item.exam_id}
              item={item}
              onPreview={handlePreview}
              onDownload={handleDownload}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
          <span className="text-sm text-muted-foreground">
            共 {total} 条记录
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
            >
              上一页
            </Button>
            <span className="text-sm text-muted-foreground px-2">
              {page} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
            >
              下一页
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
