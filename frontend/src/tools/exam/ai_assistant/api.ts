/** API calls for AI assistant */

import type {
  ChatRequest,
  ChatResponse,
  ClearThreadRequest,
  ThreadStatusResponse,
  ToolResultsRequest,
  ToolResultsResponse,
} from "./types"

const BASE = "/api/v1/ai-assistant"

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
  return res.json() as Promise<T>
}

async function apiFetchMultipart<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: { ...authHeaders(), ...init?.headers },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body?.detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export function chat(
  request: ChatRequest,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  return apiFetch(`${BASE}/chat`, {
    method: "POST",
    body: JSON.stringify(request),
    signal,
  })
}

export function chatWithFiles(
  request: ChatRequest,
  files: File[],
  signal?: AbortSignal,
): Promise<ChatResponse> {
  const formData = new FormData()
  formData.append("exam_id", request.exam_id)
  formData.append("message", request.message)
  formData.append("current_questions", JSON.stringify(request.current_questions))
  files.forEach((file) => formData.append("files", file))

  return apiFetchMultipart(`${BASE}/chat-with-files`, {
    method: "POST",
    body: formData,
    signal,
  })
}

export function submitToolResults(
  request: ToolResultsRequest,
  signal?: AbortSignal,
): Promise<ToolResultsResponse> {
  return apiFetch(`${BASE}/tool-results`, {
    method: "POST",
    body: JSON.stringify(request),
    signal,
  })
}

export function clearThread(
  request: ClearThreadRequest,
  signal?: AbortSignal,
): Promise<{ success: boolean }> {
  return apiFetch(`${BASE}/clear`, {
    method: "POST",
    body: JSON.stringify(request),
    signal,
  })
}

export function getThreadStatus(
  examId: string,
  signal?: AbortSignal,
): Promise<ThreadStatusResponse> {
  return apiFetch(
    `${BASE}/thread?exam_id=${encodeURIComponent(examId)}`,
    { signal },
  )
}
