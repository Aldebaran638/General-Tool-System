/** Types for notification module */

export interface Notification {
  id: string
  title: string
  content: string
  notification_type: string
  is_read: boolean
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
