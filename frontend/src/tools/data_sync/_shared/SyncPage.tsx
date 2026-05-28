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
import { RefreshCw, Play, CheckCircle2, XCircle, Clock, Loader2 } from "lucide-react"

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
import { Search } from "lucide-react"

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
    return <Badge className="bg-green-100 text-green-800 hover:bg-green-100"><CheckCircle2 className="mr-1 h-3 w-3" />成功</Badge>
  if (status === "failed")
    return <Badge className="bg-red-100 text-red-800 hover:bg-red-100"><XCircle className="mr-1 h-3 w-3" />失败</Badge>
  if (status === "running")
    return <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100"><Loader2 className="mr-1 h-3 w-3 animate-spin" />运行中</Badge>
  return <Badge variant="secondary"><Clock className="mr-1 h-3 w-3" />等待中</Badge>
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
      <Card>
        <CardHeader>
          <CardTitle className="text-base">手动触发</CardTitle>
          <CardDescription>增量同步：拉取全部数据并更新，不处理软删除。全量同步：拉取全部数据并更新，同时标记已消失的记录。</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-3">
          <Button
            disabled={busy}
            onClick={() => onTrigger("incremental")}
            variant="outline"
          >
            {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
            增量同步
          </Button>
          <Button
            disabled={busy}
            onClick={() => onTrigger("full")}
          >
            {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
            全量同步
          </Button>
        </CardContent>
      </Card>

      {/* Latest task summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">上次同步</CardTitle>
        </CardHeader>
        <CardContent>
          {isStatusLoading && <p className="text-muted-foreground text-sm">加载中…</p>}
          {!isStatusLoading && !latest && (
            <p className="text-muted-foreground text-sm">暂无同步记录</p>
          )}
          {latest && (
            <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
              <div><dt className="text-muted-foreground">状态</dt><dd><StatusBadge status={latest.status} /></dd></div>
              <div><dt className="text-muted-foreground">模式</dt><dd>{latest.sync_mode === "full" ? "全量" : "增量"}</dd></div>
              <div><dt className="text-muted-foreground">触发方式</dt><dd>{latest.trigger_type === "manual" ? "手动" : "定时"}</dd></div>
              <div><dt className="text-muted-foreground">开始时间</dt><dd>{fmtDate(latest.started_at)}</dd></div>
              <div><dt className="text-muted-foreground">耗时</dt><dd>{fmtDuration(latest)}</dd></div>
              <div><dt className="text-muted-foreground">拉取条数</dt><dd>{latest.fetched_count ?? "—"}</dd></div>
              <div><dt className="text-muted-foreground">新增</dt><dd className="text-green-700">{latest.created_count ?? "—"}</dd></div>
              <div><dt className="text-muted-foreground">更新</dt><dd className="text-blue-700">{latest.updated_count ?? "—"}</dd></div>
              <div><dt className="text-muted-foreground">删除/移除</dt><dd className="text-orange-600">{latest.deleted_count ?? "—"}</dd></div>
              {latest.error_message && (
                <div className="col-span-3">
                  <dt className="text-muted-foreground">错误信息</dt>
                  <dd className="mt-1 rounded bg-red-50 p-2 font-mono text-xs text-red-700 whitespace-pre-wrap">{latest.error_message}</dd>
                </div>
              )}
            </dl>
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
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
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
              <TableRow><TableCell colSpan={10} className="text-center text-muted-foreground">加载中…</TableCell></TableRow>
            )}
            {!isTasksLoading && tasks.length === 0 && (
              <TableRow><TableCell colSpan={10} className="text-center text-muted-foreground">暂无记录</TableCell></TableRow>
            )}
            {tasks.map((t) => (
              <TableRow key={t.id}>
                <TableCell className="whitespace-nowrap text-sm">{fmtDate(t.started_at)}</TableCell>
                <TableCell><Badge variant="outline">{t.sync_mode === "full" ? "全量" : "增量"}</Badge></TableCell>
                <TableCell className="text-sm text-muted-foreground">{t.trigger_type === "manual" ? "手动" : "定时"}</TableCell>
                <TableCell><StatusBadge status={t.status} /></TableCell>
                <TableCell className="text-right text-sm">{t.fetched_count ?? "—"}</TableCell>
                <TableCell className="text-right text-sm text-green-700">{t.created_count ?? "—"}</TableCell>
                <TableCell className="text-right text-sm text-blue-700">{t.updated_count ?? "—"}</TableCell>
                <TableCell className="text-right text-sm text-orange-600">{t.deleted_count ?? "—"}</TableCell>
                <TableCell className="text-sm">{fmtDuration(t)}</TableCell>
                <TableCell className="max-w-xs truncate text-xs text-red-600" title={t.error_message ?? ""}>{t.error_message ?? "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-end gap-2 text-sm">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>上一页</Button>
          <span className="text-muted-foreground">第 {page} / {totalPages} 页，共 {total} 条</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>下一页</Button>
        </div>
      )}
    </div>
  )
}

// ─── Synced data tables ──────────────────────────────────────────────────────

function MemberStatusBadge({ isActive }: { isActive: boolean }) {
  if (isActive) return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">在职</Badge>
  return <Badge className="bg-gray-100 text-gray-600 hover:bg-gray-100">已离职</Badge>
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
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
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
              <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground">加载中…</TableCell></TableRow>
            )}
            {!isLoading && data.length === 0 && (
              <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground">暂无数据，请先执行同步</TableCell></TableRow>
            )}
            {data.map((d) => (
              <TableRow key={d.id}>
                <TableCell className="font-mono text-sm">{d.id}</TableCell>
                <TableCell className="font-medium">{d.name}</TableCell>
                <TableCell className="text-muted-foreground">{d.name_en ?? "—"}</TableCell>
                <TableCell className="text-right text-sm">{d.parentid ?? "—"}</TableCell>
                <TableCell className="text-right text-sm">{d.order}</TableCell>
                <TableCell className="text-sm">{fmtDate(d.synced_at)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-end gap-2 text-sm">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>上一页</Button>
          <span className="text-muted-foreground">第 {page} / {totalPages} 页，共 {total} 条</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>下一页</Button>
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
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="搜索姓名或 userid…"
          value={search}
          onChange={(e) => { onSearchChange(e.target.value); onPageChange(1) }}
          className="pl-8"
        />
      </div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Userid</TableHead>
              <TableHead>姓名</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>创建时间</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && (
              <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">加载中…</TableCell></TableRow>
            )}
            {!isLoading && data.length === 0 && (
              <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">暂无数据，请先执行同步</TableCell></TableRow>
            )}
            {data.map((m) => (
              <TableRow key={m.userid}>
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
      {totalPages > 1 && (
        <div className="flex items-center justify-end gap-2 text-sm">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>上一页</Button>
          <span className="text-muted-foreground">第 {page} / {totalPages} 页，共 {total} 条</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>下一页</Button>
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
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        <p className="text-muted-foreground">{description}</p>
      </div>

      <Tabs defaultValue="panel">
        <TabsList>
          <TabsTrigger value="panel">操作面板</TabsTrigger>
          <TabsTrigger value="history">同步历史</TabsTrigger>
          {hasSyncedData && <TabsTrigger value="data">已同步数据</TabsTrigger>}
        </TabsList>

        <TabsContent value="panel" className="mt-4">
          <ControlPanel
            statusData={statusQuery.data}
            isStatusLoading={statusQuery.isLoading}
            onTrigger={(mode) => triggerMutation.mutate(mode)}
            isTriggerPending={triggerMutation.isPending}
          />
        </TabsContent>

        <TabsContent value="history" className="mt-4">
          <HistoryTable
            tasksData={tasksQuery.data}
            isTasksLoading={tasksQuery.isLoading}
            page={page}
            onPageChange={setPage}
          />
        </TabsContent>

        {hasSyncedData && (
          <TabsContent value="data" className="mt-4">
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
