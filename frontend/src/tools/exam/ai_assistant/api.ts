/** API calls for AI assistant */

import type {
  ChatRequest,
  ChatResponse,
  ClearThreadRequest,
  SSEEvent,
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

async function* sseStream(url: string, init?: RequestInit): AsyncGenerator<SSEEvent> {
  const res = await fetch(url, {
    ...init,
    headers: { ...authHeaders(), ...init?.headers },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body?.detail ?? `HTTP ${res.status}`)
  }
  if (!res.body) {
    throw new Error("响应体为空")
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let done = false

  while (!done) {
    const { value, done: readerDone } = await reader.read()
    done = readerDone
    buffer += decoder.decode(value, { stream: !done })
    const lines = buffer.split("\n")
    buffer = lines.pop() ?? ""

    let i = 0
    while (i < lines.length) {
      const line = lines[i]
      if (line.startsWith("event:")) {
        const dataLine = lines[i + 1]
        if (dataLine && dataLine.startsWith("data:")) {
          const data = JSON.parse(dataLine.slice(5).trim())
          yield data as SSEEvent
          i += 2
          continue
        }
      }
      i++
    }
  }
}

export function chatStream(
  request: ChatRequest,
  signal?: AbortSignal,
): AsyncGenerator<SSEEvent> {
  return sseStream(`${BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
  })
}

export function chatWithFilesStream(
  request: ChatRequest,
  files: File[],
  signal?: AbortSignal,
): AsyncGenerator<SSEEvent> {
  const formData = new FormData()
  formData.append("exam_id", request.exam_id)
  formData.append("message", request.message)
  formData.append("current_questions", JSON.stringify(request.current_questions))
  files.forEach((file) => formData.append("files", file))

  return sseStream(`${BASE}/chat-with-files/stream`, {
    method: "POST",
    body: formData,
    signal,
  })
}

export function submitToolResultsStream(
  request: ToolResultsRequest,
  signal?: AbortSignal,
): AsyncGenerator<SSEEvent> {
  return sseStream(`${BASE}/tool-results/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
  })
}
