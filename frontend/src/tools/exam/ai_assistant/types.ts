/** Types for AI assistant chat module */

import type { QuestionCreate } from "../exam_management/types"

export type QuestionType = "SINGLE_CHOICE" | "MULTIPLE_CHOICE" | "TRUE_FALSE"

export interface QuestionOptionArgs {
  option_key: string
  option_text: string
  is_correct: boolean
  sort_no: number
}

export interface CreateQuestionArgs {
  question_type: QuestionType
  stem: string
  score: number
  options: QuestionOptionArgs[]
  analysis: string
}

export interface EditQuestionArgs {
  index: number
  stem?: string
  score?: number
  options?: QuestionOptionArgs[]
  analysis?: string
}

export interface DeleteQuestionArgs {
  index: number
}

export interface SearchQuestionsArgs {
  query: string
}

export type AIToolName =
  | "create_question"
  | "edit_question"
  | "delete_question"
  | "search_questions"
  | "get_paper_summary"
  | "batch_create_questions"

export interface AIToolCall {
  id: string
  name: AIToolName
  arguments: Record<string, unknown>
}

export interface ToolResult {
  tool_call_id: string
  content: string
}

export interface ChatMessage {
  role: "user" | "assistant" | "tool"
  content: string
  tool_calls?: AIToolCall[]
  tool_call_id?: string
}

export interface ChatRequest {
  exam_id: string
  message: string
  current_questions: QuestionCreate[]
}

export interface ToolResultsRequest {
  exam_id: string
  tool_results: ToolResult[]
  current_questions: QuestionCreate[]
}

export interface ClearThreadRequest {
  exam_id: string
}

export type AIStatus = "thinking" | "tool-calling"

export interface SSEStatusEvent {
  type: "status"
  status: AIStatus
  tools?: string[]
}

export interface SSEErrorEvent {
  type: "error"
  message: string
}

export interface SSEDoneEvent {
  type: "done"
  message: string | null
  tool_calls: AIToolCall[] | null
}

export type SSEEvent = SSEStatusEvent | SSEErrorEvent | SSEDoneEvent
