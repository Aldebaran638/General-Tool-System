"use client"

import { useState } from "react"
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query"
import {
  Bell,
  Clock,
  Trash2,
  CheckCheck,
  AlertCircle,
  CalendarClock,
  FileWarning,
  Megaphone,
  Loader2,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  deleteNotification,
} from "@/tools/notification/api"
import type { Notification } from "@/tools/notification/types"

const NOTIFICATION_ICONS: Record<string, React.ReactNode> = {
  EXAM_UPCOMING: <CalendarClock className="h-4 w-4 text-blue-500" />,
  EXAM_STARTED: <Bell className="h-4 w-4 text-green-500" />,
  EXAM_INCOMPLETE: <AlertCircle className="h-4 w-4 text-amber-500" />,
  EXAM_FAILED: <FileWarning className="h-4 w-4 text-red-500" />,
  ADMIN_BROADCAST: <Megaphone className="h-4 w-4 text-purple-500" />,
}

const NOTIFICATION_LABELS: Record<string, string> = {
  EXAM_UPCOMING: "即将开始",
  EXAM_STARTED: "已开始",
  EXAM_INCOMPLETE: "未完成",
  EXAM_FAILED: "未及格",
  ADMIN_BROADCAST: "系统公告",
}

function fmtRelativeTime(s: string): string {
  const d = new Date(s)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffSec < 60) return "刚刚"
  if (diffMin < 60) return `${diffMin}分钟前`
  if (diffHour < 24) return `${diffHour}小时前`
  if (diffDay < 7) return `${diffDay}天前`
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function NotificationItem({
  notification,
  onMarkRead,
  onDelete,
}: {
  notification: Notification
  onMarkRead: (id: string) => void
  onDelete: (id: string) => void
}) {
  const icon = NOTIFICATION_ICONS[notification.notification_type] ?? (
    <Bell className="h-4 w-4 text-muted-foreground" />
  )
  const label = NOTIFICATION_LABELS[notification.notification_type] ?? "通知"

  return (
    <div
      className={`group flex items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-muted/50 ${
        notification.is_read ? "opacity-70" : "bg-primary/5"
      }`}
    >
      <div className="mt-0.5 shrink-0">{icon}</div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium truncate">{notification.title}</p>
          {!notification.is_read && (
            <Badge variant="default" className="h-1.5 w-1.5 rounded-full p-0 shrink-0" />
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
          {notification.content}
        </p>
        <div className="flex items-center justify-between mt-1.5">
          <div className="flex items-center gap-1.5">
            <Badge variant="outline" className="text-[10px] h-5 px-1">
              {label}
            </Badge>
            <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
              <Clock className="h-3 w-3" />
              {fmtRelativeTime(notification.created_at)}
            </span>
          </div>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {!notification.is_read && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={() => onMarkRead(notification.id)}
                title="标记已读"
              >
                <CheckCheck className="h-3.5 w-3.5" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 text-red-500 hover:text-red-600"
              onClick={() => onDelete(notification.id)}
              title="删除"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

interface NotificationDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function NotificationDrawer({ open, onOpenChange }: NotificationDrawerProps) {
  const queryClient = useQueryClient()
  const [page] = useState(1)
  const limit = 20

  const { data, isLoading } = useQuery({
    queryKey: ["notifications", page],
    queryFn: () => getNotifications({ page, limit }),
    enabled: open,
  })

  const markReadMutation = useMutation({
    mutationFn: (id: string) => markNotificationRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
      queryClient.invalidateQueries({ queryKey: ["notifications", "unread-count"] })
    },
  })

  const markAllReadMutation = useMutation({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
      queryClient.invalidateQueries({ queryKey: ["notifications", "unread-count"] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteNotification(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
      queryClient.invalidateQueries({ queryKey: ["notifications", "unread-count"] })
    },
  })

  const notifications = data?.data ?? []
  const total = data?.count ?? 0

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-md flex flex-col">
        <SheetHeader className="pb-2">
          <div className="flex items-center justify-between">
            <SheetTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              消息通知
              {total > 0 && (
                <Badge variant="secondary" className="text-xs">
                  {total}
                </Badge>
              )}
            </SheetTitle>
            {total > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="text-xs h-8"
                onClick={() => markAllReadMutation.mutate()}
                disabled={markAllReadMutation.isPending}
              >
                {markAllReadMutation.isPending && (
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                )}
                全部已读
              </Button>
            )}
          </div>
        </SheetHeader>

        <Separator />

        <div className="flex-1 -mx-6 px-6 overflow-y-auto">
          <div className="py-4 flex flex-col gap-2">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : notifications.length === 0 ? (
              <div className="flex flex-col items-center gap-3 py-12 text-muted-foreground">
                <div className="rounded-full bg-muted p-4">
                  <Bell className="h-6 w-6" />
                </div>
                <p className="text-sm">暂无消息</p>
              </div>
            ) : (
              notifications.map((notification: Notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onMarkRead={(id) => markReadMutation.mutate(id)}
                  onDelete={(id) => deleteMutation.mutate(id)}
                />
              ))
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
