/**
 * SyncPage — shared layout used by both WecomDepartmentSync and WecomMemberSync.
 *
 * Props:
 *   entityType  — "wecom_department" | "wecom_member"  (for display only)
 *   title       — e.g. "企微部门同步"
 *   description — subtitle
 *   onTrigger   — called with mode; returns Promise<SyncTask>
 *   statusQuery — react-query result for status endpoint
 *   tasksQuery  — react-query result for tasks endpoint
 */

import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  RefreshCw,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  Database,
  Calendar,
  ArrowUpDown,
  Activity,
  AlertCircle,
  Zap,
  RotateCw,
  Search,
  Building2,
  Users,
} from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

import type {
  SyncMode,
  SyncTask,
  SyncStatusResponse,
  SyncTasksResponse,
  WecomDepartment,
  WecomDepartmentsResponse,
  WecomMember,
  WecomMembersResponse,
} from "./types"
import { Input } from "@/components/ui/input"

// ─── helpers ─────────────────────────────────────────────────────────────────

function fmtDate(s: string | null): string {
  if (!s) return "—"
  return new Date(s).toLocaleString("zh-CN", { hour12: false })
}

function fmtDuration(task: SyncTask): string {
  if (!task.finished_at) return "—"
  const ms = new Date(task.finished_at).getTime() - new Date(task.started_at).getTime()
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`
}

function StatusBadge({ status }: { status: string }) {
  if (status === "success")
    return (
      <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
        <CheckCircle2 className="mr-1 h-3 w-3" />
        成功
      </Badge>
    )
  if (status === "failed")
    return (
      <Badge variant="outline" className="border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
        <XCircle className="mr-1 h-3 w-3" />
        失败
      </Badge>
    )
  if (status === "running")
    return (
      <Badge variant="outline" className="border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-300">
        <Loader2 className="mr-1 h-3 w-3 animate-spin" />
        运行中
      </Badge>
    )
  return (
    <Badge variant="outline" className="border-gray-200 bg-gray-50 text-gray-600 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400">
      <Clock className="mr-1 h-3 w-3" />
      等待中
    </Badge>
  )
}

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string
  value: string | number
  icon: React.ElementType
  color: string
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl bg-muted/50 p-3">
      <div className={`rounded-lg p-2 ${color}`}>
        <Icon className="h-4 w-4" />
      </div>
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-lg font-semibold">{value}</p>
      </div>
    </div>
  )
}

// ─── Status panel (tab 1) ─────────────────────────────────────────────────────

function ControlPanel({
  statusData,
  isStatusLoading,
  onTrigger,
  isTriggerPending,
}: {
  statusData: SyncStatusResponse | undefined
  isStatusLoading: boolean
  onTrigger: (mode: SyncMode) => void
  isTriggerPending: boolean
}) {
  const latest = statusData?.latest
  const isRunning = statusData?.is_running ?? false
  const busy = isRunning || isTriggerPending

  return (
    <div className="flex flex-col gap-6">
      {/* Trigger buttons */}
      <Card className="overflow-hidden">
        <div className="h-1 bg-gradient-to-r from-blue-500 to-purple-500" />
        <CardHeader>
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-primary/10 p-2">
              <Zap className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-base">手动触发同步</CardTitle>
              <CardDescription className="mt-1">
                增量同步：拉取全部数据并更新，不处理软删除。全量同步：拉取全部数据并更新，同时标记已消失的记录。
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col sm:flex-row gap-3">
          <Button
            disabled={busy}
            onClick={() => onTrigger("incremental")}
            variant="outline"
            className="flex-1 transition-all hover:border-blue-300 hover:bg-blue-50 dark:hover:border-blue-700 dark:hover:bg-blue-950"
          >
            {busy ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}
            增量同步
          </Button>
          <Button
            disabled={busy}
            onClick={() => onTrigger("full")}
            className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 transition-all"
          >
            {busy ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className={`mr-2 h-4 w-4 ${isRunning ? "animate-spin" : ""}`} />
            )}
            全量同步
          </Button>
        </CardContent>
      </Card>

      {/* Next sync schedule */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-base">定时同步计划</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {isStatusLoading && (
            <div className="space-y-3">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          )}
          {!isStatusLoading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex items-center gap-3 rounded-xl border p-4">
                <div className="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/50">
                  <RotateCw className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">下次增量同步</p>
                  <p className="font-medium text-sm">
                    {statusData?.next_incremental_sync ? (
                      <span className="text-blue-600 dark:text-blue-400">
                        {fmtDate(statusData.next_incremental_sync)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">未调度</span>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-xl border p-4">
                <div className="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/50">
                  <RotateCw className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">下次全量同步</p>
                  <p className="font-medium text-sm">
                    {statusData?.next_full_sync ? (
                      <span className="text-purple-600 dark:text-purple-400">
                        {fmtDate(statusData.next_full_sync)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">未调度</span>
                    )}
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Latest task summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-base">上次同步详情</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {isStatusLoading && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          )}
          {!isStatusLoading && !latest && (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <Database className="h-12 w-12 mb-3 opacity-50" />
              <p className="font-medium">暂无同步记录</p>
              <p className="text-sm">执行同步后将在此显示详情</p>
            </div>
          )}
          {latest && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge status={latest.status} />
                <Badge variant="outline">
                  {latest.sync_mode === "full" ? "全量同步" : "增量同步"}
                </Badge>
                <Badge variant="secondary">
                  {latest.trigger_type === "manual" ? "手动触发" : "定时触发"}
                </Badge>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <StatCard
                  label="开始时间"
                  value={fmtDate(latest.started_at).split(" ")[1] || fmtDate(latest.started_at)}
                  icon={Clock}
                  color="bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                />
                <StatCard
                  label="耗时"
                  value={fmtDuration(latest)}
                  icon={ArrowUpDown}
                  color="bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                />
                <StatCard
                  label="拉取条数"
                  value={latest.fetched_count ?? "—"}
                  icon={Database}
                  color="bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                />
                <StatCard
                  label="新增"
                  value={latest.created_count ?? "—"}
                  icon={CheckCircle2}
                  color="bg-emerald-100 text-emerald-600 dark:bg-emerald-900/50 dark:text-emerald-400"
                />
                <StatCard
                  label="更新"
                  value={latest.updated_count ?? "—"}
                  icon={RefreshCw}
                  color="bg-blue-100 text-blue-600 dark:bg-blue-900/50 dark:text-blue-400"
                />
                <StatCard
                  label="删除/移除"
                  value={latest.deleted_count ?? "—"}
                  icon={XCircle}
                  color="bg-orange-100 text-orange-600 dark:bg-orange-900/50 dark:text-orange-400"
                />
              </div>

              {latest.error_message && (
                <div className="rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950/50">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-red-800 dark:text-red-200">错误信息</p>
                      <p className="mt-1 font-mono text-xs text-red-700 dark:text-red-300 whitespace-pre-wrap">
                        {latest.error_message}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ─── History table (tab 2) ────────────────────────────────────────────────────

function HistoryTable({
  tasksData,
  isTasksLoading,
  page,
  onPageChange,
}: {
  tasksData: SyncTasksResponse | undefined
  isTasksLoading: boolean
  page: number
  onPageChange: (p: number) => void
}) {
  const tasks = tasksData?.data ?? []
  const total = tasksData?.count ?? 0
  const pageSize = 20
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardContent className="p-0">
          <div className="rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead>开始时间</TableHead>
                  <TableHead>模式</TableHead>
                  <TableHead>触发</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">拉取</TableHead>
                  <TableHead className="text-right">新增</TableHead>
                  <TableHead className="text-right">更新</TableHead>
                  <TableHead className="text-right">删除</TableHead>
                  <TableHead>耗时</TableHead>
                  <TableHead>错误</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isTasksLoading && (
                  <TableRow>
                    <TableCell colSpan={10} className="text-center py-8">
                      <div className="flex items-center justify-center gap-2 text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        加载中...
                      </div>
                    </TableCell>
                  </TableRow>
                )}
                {!isTasksLoading && tasks.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={10} className="text-center py-12">
                      <div className="flex flex-col items-center gap-2 text-muted-foreground">
                        <Database className="h-8 w-8 opacity-50" />
                        <p className="font-medium">暂无记录</p>
                        <p className="text-sm">执行同步后将在此显示历史记录</p>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
                {tasks.map((t) => (
                  <TableRow key={t.id} className="hover:bg-muted/30 transition-colors">
                    <TableCell className="whitespace-nowrap text-sm">{fmtDate(t.started_at)}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-normal">
                        {t.sync_mode === "full" ? "全量" : "增量"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {t.trigger_type === "manual" ? "手动" : "定时"}
                    </TableCell>
                    <TableCell><StatusBadge status={t.status} /></TableCell>
                    <TableCell className="text-right text-sm font-mono">{t.fetched_count ?? "—"}</TableCell>
                    <TableCell className="text-right text-sm font-mono text-emerald-600">{t.created_count ?? "—"}</TableCell>
                    <TableCell className="text-right text-sm font-mono text-blue-600">{t.updated_count ?? "—"}</TableCell>
                    <TableCell className="text-right text-sm font-mono text-orange-600">{t.deleted_count ?? "—"}</TableCell>
                    <TableCell className="text-sm font-mono">{fmtDuration(t)}</TableCell>
                    <TableCell className="max-w-[200px]">
                      {t.error_message ? (
                        <span className="text-xs text-red-600 truncate block" title={t.error_message}>
                          {t.error_message}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
      {totalPages > 1 && (
        <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
          <span className="text-sm text-muted-foreground">
            共 {total} 条记录
          </span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
              上一页
            </Button>
            <span className="text-sm text-muted-foreground px-2">
              {page} / {totalPages}
            </span>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
              下一页
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Synced data tables ──────────────────────────────────────────────────────

function MemberStatusBadge({ isActive }: { isActive: boolean }) {
  if (isActive)
    return (
      <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
        <CheckCircle2 className="mr-1 h-3 w-3" />
        在职
      </Badge>
    )
  return (
    <Badge variant="outline" className="border-gray-200 bg-gray-50 text-gray-600 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400">
      已离职
    </Badge>
  )
}

function SyncedDepartmentTable({
  data,
  isLoading,
  page,
  total,
  onPageChange,
}: {
  data: WecomDepartment[]
  isLoading: boolean
  page: number
  total: number
  onPageChange: (p: number) => void
}) {
  const pageSize = 20
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardContent className="p-0">
          <div className="rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="w-20">ID</TableHead>
                  <TableHead>名称</TableHead>
                  <TableHead>英文名</TableHead>
                  <TableHead className="text-right">上级部门 ID</TableHead>
                  <TableHead className="text-right">排序</TableHead>
                  <TableHead>同步时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8">
                      <div className="flex items-center justify-center gap-2 text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        加载中...
                      </div>
                    </TableCell>
                  </TableRow>
                )}
                {!isLoading && data.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-12">
                      <div className="flex flex-col items-center gap-2 text-muted-foreground">
                        <Building2 className="h-8 w-8 opacity-50" />
                        <p className="font-medium">暂无数据</p>
                        <p className="text-sm">请先执行同步操作</p>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
                {data.map((d) => (
                  <TableRow key={d.id} className="hover:bg-muted/30 transition-colors">
                    <TableCell className="font-mono text-sm">{d.id}</TableCell>
                    <TableCell className="font-medium">{d.name}</TableCell>
                    <TableCell className="text-muted-foreground">{d.name_en ?? "—"}</TableCell>
                    <TableCell className="text-right text-sm font-mono">{d.parentid ?? "—"}</TableCell>
                    <TableCell className="text-right text-sm font-mono">{d.order}</TableCell>
                    <TableCell className="text-sm">{fmtDate(d.synced_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
      {totalPages > 1 && (
        <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
          <span className="text-sm text-muted-foreground">
            共 {total} 条记录
          </span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
              上一页
            </Button>
            <span className="text-sm text-muted-foreground px-2">
              {page} / {totalPages}
            </span>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
              下一页
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

function SyncedMemberTable({
  data,
  isLoading,
  page,
  total,
  search,
  onSearchChange,
  onPageChange,
}: {
  data: WecomMember[]
  isLoading: boolean
  page: number
  total: number
  search: string
  onSearchChange: (v: string) => void
  onPageChange: (p: number) => void
}) {
  const pageSize = 20
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="flex flex-col gap-4">
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="搜索姓名或 userid..."
          value={search}
          onChange={(e) => {
            onSearchChange(e.target.value)
            onPageChange(1)
          }}
          className="pl-9 transition-all focus-visible:ring-2 focus-visible:ring-primary/20"
        />
      </div>
      <Card>
        <CardContent className="p-0">
          <div className="rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead>Userid</TableHead>
                  <TableHead>姓名</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>创建时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading && (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-8">
                      <div className="flex items-center justify-center gap-2 text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        加载中...
                      </div>
                    </TableCell>
                  </TableRow>
                )}
                {!isLoading && data.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-12">
                      <div className="flex flex-col items-center gap-2 text-muted-foreground">
                        <Users className="h-8 w-8 opacity-50" />
                        <p className="font-medium">暂无数据</p>
                        <p className="text-sm">请先执行同步操作</p>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
                {data.map((m) => (
                  <TableRow key={m.userid} className="hover:bg-muted/30 transition-colors">
                    <TableCell className="font-mono text-sm">{m.userid}</TableCell>
                    <TableCell className="font-medium">{m.name}</TableCell>
                    <TableCell>
                      <MemberStatusBadge isActive={m.is_active} />
                    </TableCell>
                    <TableCell className="text-sm">{fmtDate(m.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
      {totalPages > 1 && (
        <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
          <span className="text-sm text-muted-foreground">
            共 {total} 条记录
          </span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
              上一页
            </Button>
            <span className="text-sm text-muted-foreground px-2">
              {page} / {totalPages}
            </span>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
              下一页
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Exported shared page ─────────────────────────────────────────────────────

export interface SyncPageProps {
  title: string
  description: string
  statusQueryKey: string[]
  tasksQueryKey: (page: number) => string[]
  fetchStatus: () => Promise<SyncStatusResponse>
  fetchTasks: (page: number) => Promise<SyncTasksResponse>
  triggerSync: (mode: SyncMode) => Promise<SyncTask>
  /** Fetch paginated synced departments */
  fetchDepartments?: (page: number) => Promise<WecomDepartmentsResponse>
  /** Fetch paginated synced members (with optional search) */
  fetchMembers?: (page: number, q?: string) => Promise<WecomMembersResponse>
}

export function SyncPage({
  title,
  description,
  statusQueryKey,
  tasksQueryKey,
  fetchStatus,
  fetchTasks,
  triggerSync,
  fetchDepartments,
  fetchMembers,
}: SyncPageProps) {
  const [page, setPage] = useState(1)
  const [dataPage, setDataPage] = useState(1)
  const [memberSearch, setMemberSearch] = useState("")
  const queryClient = useQueryClient()

  const statusQuery = useQuery({
    queryKey: statusQueryKey,
    queryFn: fetchStatus,
    refetchInterval: (q) => (q.state.data?.is_running ? 2000 : false),
  })

  const tasksQuery = useQuery({
    queryKey: tasksQueryKey(page),
    queryFn: () => fetchTasks(page),
  })

  const triggerMutation = useMutation({
    mutationFn: triggerSync,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: statusQueryKey })
      queryClient.invalidateQueries({ queryKey: ["sync-tasks"] })
      toast.success("同步任务已触发", {
        description: "同步任务已成功提交，请稍后查看结果。",
      })
    },
    onError: (error: Error) => {
      toast.error("同步触发失败", {
        description: error.message || "无法触发同步任务，请稍后重试。",
      })
    },
  })

  const departmentsQuery = useQuery({
    queryKey: ["synced-departments", dataPage],
    queryFn: () => fetchDepartments!(dataPage),
    enabled: !!fetchDepartments,
  })

  const membersQuery = useQuery({
    queryKey: ["synced-members", dataPage, memberSearch],
    queryFn: () => fetchMembers!(dataPage, memberSearch || undefined),
    enabled: !!fetchMembers,
  })

  const hasSyncedData = !!fetchDepartments || !!fetchMembers

  return (
    <div className="flex flex-col gap-6">
      {/* Page header */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-primary/10 p-2.5">
            <Database className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
            <p className="text-muted-foreground">{description}</p>
          </div>
        </div>
      </div>

      <Tabs defaultValue="panel" className="w-full">
        <TabsList className="w-full sm:w-auto">
          <TabsTrigger value="panel" className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            操作面板
          </TabsTrigger>
          <TabsTrigger value="history" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            同步历史
          </TabsTrigger>
          {hasSyncedData && (
            <TabsTrigger value="data" className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              已同步数据
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="panel" className="mt-6">
          <ControlPanel
            statusData={statusQuery.data}
            isStatusLoading={statusQuery.isLoading}
            onTrigger={(mode) => triggerMutation.mutate(mode)}
            isTriggerPending={triggerMutation.isPending}
          />
        </TabsContent>

        <TabsContent value="history" className="mt-6">
          <HistoryTable
            tasksData={tasksQuery.data}
            isTasksLoading={tasksQuery.isLoading}
            page={page}
            onPageChange={setPage}
          />
        </TabsContent>

        {hasSyncedData && (
          <TabsContent value="data" className="mt-6">
            {fetchDepartments && (
              <SyncedDepartmentTable
                data={departmentsQuery.data?.data ?? []}
                isLoading={departmentsQuery.isLoading}
                page={dataPage}
                total={departmentsQuery.data?.count ?? 0}
                onPageChange={setDataPage}
              />
            )}
            {fetchMembers && (
              <SyncedMemberTable
                data={membersQuery.data?.data ?? []}
                isLoading={membersQuery.isLoading}
                page={dataPage}
                total={membersQuery.data?.count ?? 0}
                search={memberSearch}
                onSearchChange={setMemberSearch}
                onPageChange={setDataPage}
              />
            )}
          </TabsContent>
        )}
      </Tabs>
    </div>
  )
}
