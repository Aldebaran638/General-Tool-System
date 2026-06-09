/** Types for notification module */

export interface Notification {
  id: string
  title: string
  content: string
  notification_type: "EXAM_UPCOMING" | "EXAM_STARTED" | "EXAM_INCOMPLETE" | "EXAM_FAILED" | "ADMIN_BROADCAST"
  is_read: boolean
  exam_id: string | null
  exam_name: string | null
  created_at: string
  read_at: string | null
}

export interface NotificationsResponse {
  data: Notification[]
  count: number
}

export interface UnreadCountResponse {
  count: number
}
