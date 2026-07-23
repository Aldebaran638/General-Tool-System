import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  BellRing,
  CalendarClock,
  Pencil,
  Plus,
  Send,
  ShieldAlert,
  Trash2,
} from "lucide-react"
import { useState } from "react"

import {
  OkrService,
  type ReminderRuleInput,
  type ReminderRulePublic,
  WorkReportsService,
} from "@/client"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import ReminderRuleDialog from "./ReminderRuleDialog"

const WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

const formatRule = (rule: ReminderRulePublic) => {
  const clock = rule.local_time.slice(0, 5)
  if (rule.report_type === "weekly") {
    return `每${WEEKDAYS[(rule.weekday ?? 1) - 1]} ${clock}`
  }
  return rule.is_last_day
    ? `每月最后一天 ${clock}`
    : `每月 ${rule.month_day} 日 ${clock}`
}

const WorkReportReminders = () => {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [ruleDialogOpen, setRuleDialogOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<ReminderRulePublic | null>(
    null,
  )
  const [deletingRule, setDeletingRule] = useState<ReminderRulePublic | null>(
    null,
  )
  const [testRecipientId, setTestRecipientId] = useState("")

  const isAdmin = Boolean(user?.is_superuser)
  const rulesQuery = useQuery({
    queryKey: ["work-report-reminder-rules"],
    queryFn: WorkReportsService.readReminderRules,
    enabled: isAdmin,
  })
  const runsQuery = useQuery({
    queryKey: ["work-report-reminder-runs"],
    queryFn: () => WorkReportsService.readReminderRuns({ limit: 50 }),
    enabled: isAdmin,
  })
  const timezonesQuery = useQuery({
    queryKey: ["work-report-reminder-timezones"],
    queryFn: WorkReportsService.readReminderTimezones,
    enabled: isAdmin,
  })
  const testRecipientsQuery = useQuery({
    queryKey: ["work-report-reminder-test-recipients"],
    queryFn: WorkReportsService.readReminderTestRecipients,
    enabled: isAdmin,
  })
  const recipientsQuery = useQuery({
    queryKey: ["work-report-reminder-recipients"],
    queryFn: WorkReportsService.readReminderRecipients,
    enabled: isAdmin,
  })
  const departmentsQuery = useQuery({
    queryKey: ["departments"],
    queryFn: () => OkrService.readDepartments(),
    enabled: isAdmin,
  })

  const refresh = () =>
    Promise.all([
      queryClient.invalidateQueries({
        queryKey: ["work-report-reminder-rules"],
      }),
      queryClient.invalidateQueries({
        queryKey: ["work-report-reminder-runs"],
      }),
    ])

  const saveMutation = useMutation({
    mutationFn: (requestBody: ReminderRuleInput) =>
      editingRule
        ? WorkReportsService.updateReminderRule({
            ruleId: editingRule.id,
            requestBody,
          })
        : WorkReportsService.createReminderRule({ requestBody }),
    onSuccess: async () => {
      await refresh()
      setRuleDialogOpen(false)
      setEditingRule(null)
      showSuccessToast("提醒规则已保存")
    },
    onError: handleError.bind(showErrorToast),
  })
  const deleteMutation = useMutation({
    mutationFn: (ruleId: string) =>
      WorkReportsService.deleteReminderRule({ ruleId }),
    onSuccess: async () => {
      await refresh()
      setDeletingRule(null)
      showSuccessToast("提醒规则已删除")
    },
    onError: handleError.bind(showErrorToast),
  })
  const testMutation = useMutation({
    mutationFn: () =>
      WorkReportsService.testReminder({
        requestBody: { user_id: testRecipientId },
      }),
    onSuccess: () => showSuccessToast("测试卡片已发送给指定用户"),
    onError: handleError.bind(showErrorToast),
  })

  if (user && !user.is_superuser) {
    return (
      <Alert variant="destructive">
        <ShieldAlert className="h-4 w-4" />
        <AlertTitle>无权访问</AlertTitle>
        <AlertDescription>仅超级管理员可以管理汇报提醒。</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold">
            <BellRing className="h-6 w-6 text-primary" />
            工作汇报提醒
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            仅向当前周期尚未提交周报或月报的规则成员发送消息卡片。
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <div className="min-w-72 space-y-1.5">
            <Label htmlFor="test-reminder-recipient">测试接收人</Label>
            <select
              id="test-reminder-recipient"
              className="border-input bg-background h-9 w-full rounded-md border px-3 text-sm"
              value={testRecipientId}
              onChange={(event) => setTestRecipientId(event.target.value)}
            >
              <option value="">请选择，不会默认发送</option>
              {testRecipientsQuery.data?.data.map((recipient) => (
                <option key={recipient.id} value={recipient.id}>
                  {recipient.name || recipient.email}（{recipient.email}）
                </option>
              ))}
            </select>
          </div>
          <LoadingButton
            variant="outline"
            disabled={!testRecipientId}
            loading={testMutation.isPending}
            onClick={() => testMutation.mutate()}
          >
            <Send className="h-4 w-4" />
            发送测试卡片
          </LoadingButton>
        </div>
      </div>

      <Tabs defaultValue="rules">
        <TabsList>
          <TabsTrigger value="rules">提醒规则</TabsTrigger>
          <TabsTrigger value="runs">发送记录</TabsTrigger>
        </TabsList>

        <TabsContent value="rules" className="space-y-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="font-medium">当前提醒规则</h2>
              <p className="text-sm text-muted-foreground">
                每条规则拥有独立的发送时间和适用成员。
              </p>
            </div>
            <Button
              onClick={() => {
                setEditingRule(null)
                setRuleDialogOpen(true)
              }}
            >
              <Plus className="h-4 w-4" />
              新增提醒规则
            </Button>
          </div>

          <div className="grid gap-3">
            {rulesQuery.data?.data.length === 0 ? (
              <Card>
                <CardContent className="py-10 text-center">
                  <BellRing className="mx-auto h-8 w-8 text-muted-foreground/60" />
                  <p className="mt-3 font-medium">尚未创建提醒规则</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    创建规则后，系统才会在指定时间自动检查并发送提醒。
                  </p>
                </CardContent>
              </Card>
            ) : null}
            {rulesQuery.data?.data.map((rule) => (
              <Card key={rule.id}>
                <CardContent className="flex flex-wrap items-center justify-between gap-4 py-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2 font-medium">
                      <CalendarClock className="h-4 w-4 text-primary" />
                      {rule.report_type === "weekly" ? "周报" : "月报"} ·{" "}
                      {formatRule(rule)}
                      <Badge variant={rule.enabled ? "default" : "secondary"}>
                        {rule.enabled ? "已启用" : "已停用"}
                      </Badge>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {rule.timezone} · 适用成员{" "}
                      {rule.recipient_user_ids?.length ?? 0} 人
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEditingRule(rule)
                        setRuleDialogOpen(true)
                      }}
                    >
                      <Pencil className="h-4 w-4" />
                      编辑
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      disabled={deleteMutation.isPending}
                      onClick={() => setDeletingRule(rule)}
                    >
                      <Trash2 className="h-4 w-4" />
                      删除
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="runs" className="space-y-3">
          {runsQuery.data?.data.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                暂无发送记录。
              </CardContent>
            </Card>
          ) : null}
          {runsQuery.data?.data.map((run) => {
            const issues = run.deliveries.filter(
              (delivery) => delivery.status !== "sent",
            )
            return (
              <Card key={run.id}>
                <CardHeader>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <CardTitle className="text-base">
                      {run.report_type === "weekly" ? "周报" : "月报"} ·{" "}
                      {run.period_start} 至 {run.period_end}
                    </CardTitle>
                    <Badge
                      variant={run.failed_count ? "destructive" : "secondary"}
                    >
                      {run.status === "completed" ? "已完成" : "部分失败"}
                    </Badge>
                  </div>
                  <CardDescription>
                    计划时间：
                    {new Date(run.scheduled_for).toLocaleString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-4 text-sm">
                    <span>目标 {run.target_count}</span>
                    <span className="text-green-600">
                      成功 {run.sent_count}
                    </span>
                    <span className="text-destructive">
                      失败 {run.failed_count}
                    </span>
                    <span>跳过 {run.skipped_count}</span>
                  </div>
                  {issues.length ? (
                    <details className="mt-3 text-sm">
                      <summary className="cursor-pointer">
                        查看失败或跳过详情
                      </summary>
                      <div className="mt-2 space-y-2">
                        {issues.map((issue) => (
                          <div key={issue.id} className="rounded border p-2">
                            <span className="font-medium">
                              {issue.user_name ?? "未知用户"}
                            </span>
                            ：{issue.error_message ?? issue.error_code}
                          </div>
                        ))}
                      </div>
                    </details>
                  ) : null}
                </CardContent>
              </Card>
            )
          })}
        </TabsContent>
      </Tabs>

      <ReminderRuleDialog
        open={ruleDialogOpen}
        onOpenChange={(open) => {
          if (!saveMutation.isPending) {
            setRuleDialogOpen(open)
            if (!open) setEditingRule(null)
          }
        }}
        rule={editingRule}
        recipients={recipientsQuery.data?.data ?? []}
        departments={departmentsQuery.data?.data ?? []}
        timezones={timezonesQuery.data?.data ?? ["Asia/Shanghai"]}
        saving={saveMutation.isPending}
        onSave={(payload) => saveMutation.mutate(payload)}
      />

      <AlertDialog
        open={Boolean(deletingRule)}
        onOpenChange={(open) => {
          if (!open) setDeletingRule(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>删除提醒规则？</AlertDialogTitle>
            <AlertDialogDescription>
              删除后，该规则将不再自动发送
              {deletingRule?.report_type === "weekly" ? "周报" : "月报"}
              提醒。已有发送记录不会被删除。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-white hover:bg-destructive/90"
              disabled={deleteMutation.isPending}
              onClick={() => {
                if (deletingRule) deleteMutation.mutate(deletingRule.id)
              }}
            >
              确认删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export default WorkReportReminders
