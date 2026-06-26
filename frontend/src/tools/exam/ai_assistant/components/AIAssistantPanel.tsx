import { useRef, useState } from "react"
import { Trash2, X } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { AetherSpectrum } from "./AetherSpectrum"
import { ChatInput } from "./ChatInput"
import { ChatMessageList } from "./ChatMessageList"
import { chat, chatWithFiles, clearThread, submitToolResults } from "../api"
import type {
  AIToolCall,
  ChatMessage,
  CreateQuestionArgs,
  EditQuestionArgs,
  DeleteQuestionArgs,
  SearchQuestionsArgs,
  ToolResult,
} from "../types"
import type { QuestionCreate } from "../../exam_management/types"

interface AIAssistantPanelProps {
  examId: string
  open: boolean
  onOpenChange: (open: boolean) => void
  questions: QuestionCreate[]
  onQuestionsChange: (questions: QuestionCreate[]) => void
  className?: string
}

const CHAT_TIMEOUT_MS = 130000

function buildQuestionCreate(args: CreateQuestionArgs, sortNo: number): QuestionCreate {
  const options = args.options.map((o, i) => ({
    option_key: o.option_key || String.fromCharCode(65 + i),
    option_text: o.option_text,
    is_correct: o.is_correct,
    sort_no: o.sort_no ?? i + 1,
  }))

  if (args.question_type === "TRUE_FALSE" && options.length === 0) {
    options.push(
      { option_key: "A", option_text: "正确", is_correct: true, sort_no: 1 },
      { option_key: "B", option_text: "错误", is_correct: false, sort_no: 2 },
    )
  }

  return {
    question_type: args.question_type,
    stem: args.stem,
    score: args.score,
    sort_no: sortNo,
    analysis: args.analysis,
    options,
  }
}

function applyToolCalls(
  toolCalls: AIToolCall[],
  questions: QuestionCreate[],
): { newQuestions: QuestionCreate[]; results: ToolResult[] } {
  let newQuestions = [...questions]
  const results: ToolResult[] = []

  for (const tc of toolCalls) {
    try {
      switch (tc.name) {
        case "create_question": {
          const args = tc.arguments as unknown as CreateQuestionArgs
          const q = buildQuestionCreate(args, newQuestions.length + 1)
          newQuestions = [...newQuestions, q]
          results.push({
            tool_call_id: tc.id,
            content: `已创建第 ${q.sort_no} 题：${q.stem.slice(0, 50)}${q.stem.length > 50 ? "..." : ""}`,
          })
          break
        }
        case "batch_create_questions": {
          const args = tc.arguments as { questions: CreateQuestionArgs[] }
          let added = 0
          for (const qArgs of args.questions) {
            const q = buildQuestionCreate(qArgs, newQuestions.length + 1)
            newQuestions = [...newQuestions, q]
            added++
          }
          results.push({ tool_call_id: tc.id, content: `已批量创建 ${added} 道题目` })
          break
        }
        case "edit_question": {
          const args = tc.arguments as unknown as EditQuestionArgs
          const idx = args.index
          if (idx < 0 || idx >= newQuestions.length) {
            throw new Error(`索引 ${idx} 超出范围`)
          }
          const patch: Partial<QuestionCreate> = {}
          if (args.stem !== undefined) patch.stem = args.stem
          if (args.score !== undefined) patch.score = args.score
          if (args.analysis !== undefined) patch.analysis = args.analysis
          if (args.options !== undefined) {
            patch.options = args.options.map((o, i) => ({
              option_key: o.option_key || String.fromCharCode(65 + i),
              option_text: o.option_text,
              is_correct: o.is_correct,
              sort_no: o.sort_no ?? i + 1,
            }))
          }
          newQuestions = newQuestions.map((q, i) =>
            i === idx ? { ...q, ...patch } : q,
          )
          results.push({ tool_call_id: tc.id, content: `已编辑第 ${idx + 1} 题` })
          break
        }
        case "delete_question": {
          const args = tc.arguments as unknown as DeleteQuestionArgs
          const idx = args.index
          if (idx < 0 || idx >= newQuestions.length) {
            throw new Error(`索引 ${idx} 超出范围`)
          }
          newQuestions = newQuestions
            .filter((_, i) => i !== idx)
            .map((q, i) => ({ ...q, sort_no: i + 1 }))
          results.push({ tool_call_id: tc.id, content: `已删除第 ${idx + 1} 题` })
          break
        }
        case "search_questions": {
          const args = tc.arguments as unknown as SearchQuestionsArgs
          const query = args.query.toLowerCase()
          const indices = newQuestions
            .map((q, i) => ({ q, i }))
            .filter(({ q }) => q.stem.toLowerCase().includes(query))
            .map(({ i }) => i + 1)
          results.push({
            tool_call_id: tc.id,
            content: `匹配题号：${indices.join(", ") || "无"}`,
          })
          break
        }
        case "get_paper_summary": {
          const total = newQuestions.reduce((s, q) => s + q.score, 0)
          const counts = {
            SINGLE_CHOICE: newQuestions.filter((q) => q.question_type === "SINGLE_CHOICE").length,
            MULTIPLE_CHOICE: newQuestions.filter((q) => q.question_type === "MULTIPLE_CHOICE").length,
            TRUE_FALSE: newQuestions.filter((q) => q.question_type === "TRUE_FALSE").length,
          }
          results.push({
            tool_call_id: tc.id,
            content: `共 ${newQuestions.length} 题，总分 ${total}；单选 ${counts.SINGLE_CHOICE}，多选 ${counts.MULTIPLE_CHOICE}，判断 ${counts.TRUE_FALSE}`,
          })
          break
        }
        default: {
          results.push({
            tool_call_id: tc.id,
            content: `未知工具：${tc.name}`,
          })
        }
      }
    } catch (e) {
      results.push({
        tool_call_id: tc.id,
        content: `执行失败：${(e as Error).message}`,
      })
    }
  }

  return { newQuestions, results }
}

export function AIAssistantPanel({
  examId,
  onOpenChange,
  questions,
  onQuestionsChange,
  className,
}: AIAssistantPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const abortControllerRef = useRef<AbortController | null>(null)

  function cancelCurrentRequest() {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
  }

  async function handleSend(message: string, files: File[]) {
    if (isLoading) return

    const userMsg: ChatMessage = { role: "user", content: message || `已上传 ${files.length} 个文件` }
    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)

    const controller = new AbortController()
    abortControllerRef.current = controller
    const timeoutId = window.setTimeout(() => {
      controller.abort()
    }, CHAT_TIMEOUT_MS)

    const request = {
      exam_id: examId,
      message: message || "请根据上传的文件内容生成相关考试题目。",
      current_questions: questions,
    }

    try {
      const response =
        files.length > 0
          ? await chatWithFiles(request, files, controller.signal)
          : await chat(request, controller.signal)

      if (response.tool_calls && response.tool_calls.length > 0) {
        const assistantMsg: ChatMessage = {
          role: "assistant",
          content: response.message ?? "",
          tool_calls: response.tool_calls,
        }
        setMessages((prev) => [...prev, assistantMsg])

        const { newQuestions, results } = applyToolCalls(response.tool_calls, questions)
        onQuestionsChange(newQuestions)

        const toolResponse = await submitToolResults(
          {
            exam_id: examId,
            tool_results: results,
            current_questions: newQuestions,
          },
          controller.signal,
        )

        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: toolResponse.message ?? "已完成" },
        ])
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: response.message ?? "" },
        ])
      }
    } catch (e) {
      const err = e as Error
      if (err.name === "AbortError") {
        toast.error("请求超时", {
          description: "大模型服务响应过慢，请稍后重试",
        })
      } else {
        toast.error("AI 助手出错", {
          description: err.message,
        })
      }
    } finally {
      window.clearTimeout(timeoutId)
      abortControllerRef.current = null
      setIsLoading(false)
    }
  }

  async function handleClear() {
    cancelCurrentRequest()
    try {
      await clearThread({ exam_id: examId })
      setMessages([])
      setAttachedFiles([])
      toast.success("上下文已清空")
    } catch (e) {
      toast.error("清空失败", { description: (e as Error).message })
    }
  }

  return (
    <div className={`flex flex-col bg-background ${className ?? ""}`}>
      <div className="p-4 border-b flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <AetherSpectrum state={isLoading ? "thinking" : "idle"} size={28} />
          <span className="text-base font-semibold">AI 组卷助手</span>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleClear}
            title="清空上下文"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => {
              cancelCurrentRequest()
              onOpenChange(false)
            }}
            title="关闭"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <ChatMessageList messages={messages} isLoading={isLoading} />

      <ChatInput
        onSend={handleSend}
        onCancel={isLoading ? cancelCurrentRequest : undefined}
        disabled={isLoading}
        files={attachedFiles}
        onFilesChange={setAttachedFiles}
        accept=".pdf,.docx,.txt,.md,.csv,.xlsx"
      />
    </div>
  )
}
