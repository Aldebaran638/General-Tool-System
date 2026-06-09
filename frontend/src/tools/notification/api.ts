/** API calls for notification module */

import type { NotificationsResponse, UnreadCountResponse } from "./types"

const BASE = "/api/v1/notifications"

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("access_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...init?.headers },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body?.detail ?? `HTTP ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

// ─── Notifications ──────────────────────────────────────────────────────────

export function getNotifications(params?: {
  page?: number
  limit?: number
  is_read?: boolean
}): Promise<NotificationsResponse> {
  const p = new URLSearchParams()
  if (params?.page) p.set("page", String(params.page))
  if (params?.limit) p.set("limit", String(params.limit))
  if (params?.is_read !== undefined) p.set("is_read", String(params.is_read))
  return apiFetch(`${BASE}?${p}`)
}

export function getUnreadCount(): Promise<UnreadCountResponse> {
  return apiFetch(`${BASE}/unread-count`)
}

export function markNotificationRead(notificationId: string): Promise<void> {
  return apiFetch(`${BASE}/${notificationId}/read`, { method: "POST" })
}

export function markAllNotificationsRead(): Promise<void> {
  return apiFetch(`${BASE}/read-all`, { method: "POST" })
}

export function deleteNotification(notificationId: string): Promise<void> {
  return apiFetch(`${BASE}/${notificationId}`, { method: "DELETE" })
}
