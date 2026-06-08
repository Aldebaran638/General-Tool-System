/**
 * Exam Taking Page — for users to answer exam questions
 */

import { useState, useEffect, useCallback, useRef } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate, useParams } from "@tanstack/react-router"
import { toast } from "sonner"
import {
  Clock,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  ArrowRight,
  Loader2,
  Send,
  AlertTriangle,
  BookOpen,
  Trophy,
  Target,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
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

import {
  fetchExamPaper,
  startExam,
  submitExamAnswers,
  type ExamPaper,
  type ExamQuestion,
  type SubmitAnswer,
  type SubmitResult,
} from "../api"

function Timer({
  totalMinutes,
  onTimeUp,
}: {
  totalMinutes: number
  onTimeUp: () => void
}) {
  const [secondsLeft, setSecondsLeft] = useState(totalMinutes * 60)
  const onTimeUpRef = useRef(onTimeUp)
  onTimeUpRef.current = onTimeUp

  useEffect(() => {
    const endTime = Date.now() + totalMinutes * 60 * 1000

    const timer = setInterval(() => {
      const remaining = Math.max(0, Math.round((endTime - Date.now()) / 1000))
      setSecondsLeft(remaining)
      if (remaining <= 0) {
        clearInterval(timer)
        onTimeUpRef.current()
      }
    }, 1000)

    return () => clearInterval(timer)
  }, [totalMinutes])

  const hours = Math.floor(secondsLeft / 3600)
  const minutes = Math.floor((secondsLeft % 3600) / 60)
  const seconds = secondsLeft % 60

  const isUrgent = secondsLeft < 300 // Last 5 minutes
  const isCritical = secondsLeft < 60 // Last minute

  const progressPercent = (secondsLeft / (totalMinutes * 60)) * 100

  return (
    <div className="flex flex-col items-end gap-2">
      <div
        className={`flex items-center gap-2.5 rounded-xl px-4 py-2.5 font-mono text-lg font-semibold transition-all duration-300 ${
          isCritical
            ? "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300 animate-pulse"
            : isUrgent
              ? "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
              : "bg-card border text-foreground"
        }`}
      >
        <Clock className={`h-5 w-5 ${isUrgent ? "animate-pulse" : ""}`} />
        <span>
          {hours > 0 && `${hours}:`}
          {minutes.toString().padStart(2, "0")}:
          {seconds.toString().padStart(2, "0")}
        </span>
      </div>
      {/* Time progress bar */}
      <div className="w-32 h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ${
            isCritical
              ? "bg-red-500"
              : isUrgent
                ? "bg-amber-500"
                : "bg-emerald-500"
          }`}
          style={{ width: `${progressPercent}%` }}
        />
      </div>
      {isUrgent && (
        <span
          className={`text-xs font-medium ${isCritical ? "text-red-600" : "text-amber-600"}`}
        >
          {isCritical ? "即将超时！" : "时间不多了"}
        </span>
      )}
    </div>
  )
}

function QuestionCard({
  question,
  index,
  selectedOptions,
  onSelectionChange,
}: {
  question: ExamQuestion
  index: number
  selectedOptions: string[]
  onSelectionChange: (optionIds: string[]) => void
}) {
  const isMultiple = question.question_type === "MULTIPLE_CHOICE"
  const isSingle = question.question_type === "SINGLE_CHOICE"
  const isTrueFalse = question.question_type === "TRUE_FALSE"

  const handleSingleChange = (optionId: string) => {
    onSelectionChange([optionId])
  }

  const handleMultipleChange = (optionId: string, checked: boolean) => {
    const normalizedOptions = selectedOptions.filter((id) => id !== optionId)
    if (checked) {
      onSelectionChange([...normalizedOptions, optionId])
    } else {
      onSelectionChange(normalizedOptions)
    }
  }

  const getQuestionTypeBadge = () => {
    if (isSingle) return { label: "单选题", variant: "default" as const }
    if (isMultiple) return { label: "多选题", variant: "secondary" as const }
    return { label: "判断题", variant: "outline" as const }
  }

  const typeBadge = getQuestionTypeBadge()

  return (
    <Card className="overflow-hidden border-0 shadow-lg bg-gradient-to-br from-card to-card/50">
      <CardHeader className="bg-muted/30 pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-primary text-primary-foreground font-bold text-sm">
                {index + 1}
              </div>
              <Badge variant={typeBadge.variant} className="font-normal">
                {typeBadge.label}
              </Badge>
              <Badge variant="outline" className="ml-auto">
                <Target className="mr-1 h-3 w-3" />
                {question.score} 分
              </Badge>
            </div>
            <CardTitle className="text-base font-medium leading-relaxed">
              {question.stem}
            </CardTitle>
          </div>
        </div>
        {isMultiple && (
          <p className="text-xs text-muted-foreground mt-2">
            （本题为多选题，可选择多个答案）
          </p>
        )}
      </CardHeader>
      <CardContent className="pt-6">
        {(isSingle || isTrueFalse) && (
          <RadioGroup
            name={`question-${question.id}`}
            value={selectedOptions[0] || ""}
            onValueChange={handleSingleChange}
          >
            <div className="space-y-3">
              {question.options.map((option) => {
                const inputId = `${question.id}-${option.id}`
                const isSelected = selectedOptions[0] === option.id

                return (
                  <Label
                    key={option.id}
                    htmlFor={inputId}
                    className={`group relative flex items-center space-x-4 rounded-xl border-2 p-4 transition-all duration-200 cursor-pointer ${
                      isSelected
                        ? "border-primary bg-primary/5 shadow-sm"
                        : "border-transparent bg-muted/50 hover:bg-muted hover:border-muted-foreground/20"
                    }`}
                  >
                    <div
                      className={`flex items-center justify-center h-8 w-8 rounded-lg text-sm font-medium transition-colors ${
                        isSelected
                          ? "bg-primary text-primary-foreground"
                          : "bg-background border-2 border-muted-foreground/20 group-hover:border-primary/50"
                      }`}
                    >
                      {option.option_key}
                    </div>
                    <RadioGroupItem
                      value={option.id}
                      id={inputId}
                      className="sr-only"
                    />
                    <span className="flex-1 cursor-pointer text-sm leading-relaxed">
                      {option.option_text}
                    </span>
                    {isSelected && (
                      <CheckCircle2 className="h-5 w-5 text-primary flex-shrink-0" />
                    )}
                  </Label>
                )
              })}
            </div>
          </RadioGroup>
        )}

        {isMultiple && (
          <div className="space-y-3">
            {question.options.map((option) => {
              const inputId = `${question.id}-${option.id}`
              const isSelected = selectedOptions.includes(option.id)

              return (
                <div
                  key={option.id}
                  className={`group relative flex items-center space-x-4 rounded-xl border-2 p-4 transition-all duration-200 cursor-pointer ${
                    isSelected
                      ? "border-primary bg-primary/5 shadow-sm"
                      : "border-transparent bg-muted/50 hover:bg-muted hover:border-muted-foreground/20"
                  }`}
                  onClick={() => handleMultipleChange(option.id, !isSelected)}
                  role="checkbox"
                  aria-checked={isSelected}
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (event.key === " " || event.key === "Enter") {
                      event.preventDefault()
                      handleMultipleChange(option.id, !isSelected)
                    }
                  }}
                >
                  <div
                    className={`flex items-center justify-center h-8 w-8 rounded-lg text-sm font-medium transition-colors ${
                      isSelected
                        ? "bg-primary text-primary-foreground"
                        : "bg-background border-2 border-muted-foreground/20 group-hover:border-primary/50"
                    }`}
                  >
                    {option.option_key}
                  </div>
                  <Checkbox
                    id={inputId}
                    checked={isSelected}
                    onCheckedChange={(checked) =>
                      handleMultipleChange(option.id, checked as boolean)
                    }
                    onClick={(event) => event.stopPropagation()}
                    className="sr-only"
                  />
                  <Label
                    htmlFor={inputId}
                    onClick={(event) => event.stopPropagation()}
                    className="flex-1 cursor-pointer text-sm leading-relaxed"
                  >
                    {option.option_text}
                  </Label>
                  {isSelected && (
                    <CheckCircle2 className="h-5 w-5 text-primary flex-shrink-0" />
                  )}
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function ResultCard({ result }: { result: SubmitResult }) {
  const percentage = Math.round((result.total_score / result.max_score) * 100)

  return (
    <Card className="max-w-lg mx-auto overflow-hidden border-0 shadow-xl">
      <div
        className={`h-2 ${result.passed ? "bg-gradient-to-r from-emerald-500 to-teal-500" : "bg-gradient-to-r from-red-500 to-orange-500"}`}
      />
      <CardHeader className="text-center pb-2">
        <CardTitle className="text-2xl">考试结果</CardTitle>
      </CardHeader>
      <CardContent className="space-y-8">
        {/* Score circle */}
        <div className="flex flex-col items-center">
          <div
            className={`relative flex items-center justify-center w-32 h-32 rounded-full ${
              result.passed
                ? "bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-950 dark:to-teal-950"
                : "bg-gradient-to-br from-red-100 to-orange-100 dark:from-red-950 dark:to-orange-950"
            }`}
          >
            {result.passed ? (
              <CheckCircle2 className="h-16 w-16 text-emerald-500" />
            ) : (
              <XCircle className="h-16 w-16 text-red-500" />
            )}
          </div>
          <div className="mt-4 text-center">
            <p className="text-4xl font-bold">
              {result.total_score}
              <span className="text-lg text-muted-foreground font-normal">
                {" "}
                / {result.max_score}
              </span>
            </p>
            <p className="text-muted-foreground mt-1">正确率：{percentage}%</p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>得分进度</span>
            <span>{percentage}%</span>
          </div>
          <Progress value={percentage} className="h-3" />
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-3 gap-4">
          <div className="flex flex-col items-center p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/50">
            <Trophy className="h-6 w-6 text-emerald-600 mb-2" />
            <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-300">
              {result.correct_count}
            </p>
            <p className="text-xs text-muted-foreground">答对</p>
          </div>
          <div className="flex flex-col items-center p-4 rounded-xl bg-blue-50 dark:bg-blue-950/50">
            <BookOpen className="h-6 w-6 text-blue-600 mb-2" />
            <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">
              {result.total_count}
            </p>
            <p className="text-xs text-muted-foreground">总题数</p>
          </div>
          <div className="flex flex-col items-center p-4 rounded-xl bg-purple-50 dark:bg-purple-950/50">
            <Target className="h-6 w-6 text-purple-600 mb-2" />
            <p className="text-2xl font-bold text-purple-700 dark:text-purple-300">
              {result.total_count - result.correct_count}
            </p>
            <p className="text-xs text-muted-foreground">答错</p>
          </div>
        </div>

        {/* Pass/Fail message */}
        <div
          className={`text-center p-5 rounded-xl ${
            result.passed
              ? "bg-gradient-to-r from-emerald-50 to-teal-50 text-emerald-800 dark:from-emerald-950/50 dark:to-teal-950/50 dark:text-emerald-200"
              : "bg-gradient-to-r from-red-50 to-orange-50 text-red-800 dark:from-red-950/50 dark:to-orange-950/50 dark:text-red-200"
          }`}
        >
          <p className="text-lg font-semibold">
            {result.passed ? "恭喜通过考试！" : "很遗憾，未达到及格线"}
          </p>
          <p className="text-sm mt-1 opacity-80">
            {result.passed
              ? "您的表现非常出色，继续保持！"
              : "请继续努力，下次一定能通过！"}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

function LoadingSkeleton() {
  return (
    <div className="container mx-auto py-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div className="space-y-2">
          <div className="h-8 w-64 bg-muted rounded animate-pulse" />
          <div className="h-4 w-48 bg-muted rounded animate-pulse" />
        </div>
        <div className="h-12 w-32 bg-muted rounded-xl animate-pulse" />
      </div>
      <div className="mb-6">
        <div className="h-2 w-full bg-muted rounded animate-pulse" />
      </div>
      <Card className="overflow-hidden">
        <CardHeader className="bg-muted/30 pb-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-8 w-8 bg-muted rounded-lg animate-pulse" />
            <div className="h-6 w-20 bg-muted rounded animate-pulse" />
            <div className="h-6 w-16 bg-muted rounded animate-pulse ml-auto" />
          </div>
          <div className="h-6 w-full bg-muted rounded animate-pulse" />
        </CardHeader>
        <CardContent className="pt-6 space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-muted rounded-xl animate-pulse" />
          ))}
        </CardContent>
      </Card>
    </div>
  )
}

export function ExamTakingPage() {
  const { examId } = useParams({ from: "/_layout/my-exams/$examId" })
  const navigate = useNavigate()

  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string[]>>({})
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState<SubmitResult | null>(null)
  const [showSubmitDialog, setShowSubmitDialog] = useState(false)
  const [unansweredSubmitConfirmed, setUnansweredSubmitConfirmed] =
    useState(false)
  const [attemptId, setAttemptId] = useState<string | null>(null)

  const paperQuery = useQuery<ExamPaper>({
    queryKey: ["exam-paper", examId],
    queryFn: () => fetchExamPaper(examId),
  })

  const queryClient = useQueryClient()

  // Protect against accidental page refresh/close
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (!submitted && attemptId) {
        e.preventDefault()
        e.returnValue = ""
      }
    }
    window.addEventListener("beforeunload", handler)
    return () => window.removeEventListener("beforeunload", handler)
  }, [submitted, attemptId])

  // Start exam on mount
  const startMutation = useMutation({
    mutationFn: () => startExam(examId),
    onSuccess: (data) => {
      setAttemptId(data.attempt_id)
    },
    onError: (error: Error) => {
      toast.error(`开始考试失败: ${error.message}`)
    },
  })

  useEffect(() => {
    if (!attemptId) {
      startMutation.mutate()
    }
  }, [])

  const submitMutation = useMutation({
    mutationFn: (answers: SubmitAnswer[]) => {
      if (!attemptId) throw new Error("考试未开始")
      return submitExamAnswers(examId, attemptId, answers)
    },
    onSuccess: (data) => {
      setResult(data)
      setSubmitted(true)
      // Invalidate my-exams cache to refresh status
      queryClient.invalidateQueries({ queryKey: ["my-exams"] })
    },
    onError: (error: Error) => {
      toast.error(`提交失败: ${error.message}`)
    },
  })

  const paper = paperQuery.data
  const questions = paper?.questions ?? []
  const totalQuestions = questions.length

  const handleSelectionChange = useCallback(
    (questionId: string, optionIds: string[]) => {
      setAnswers((prev) => ({ ...prev, [questionId]: optionIds }))
    },
    [],
  )

  const handleSubmit = useCallback(() => {
    if (!paper || submitMutation.isPending) return

    const submitAnswers: SubmitAnswer[] = questions.map((q) => ({
      question_id: q.id,
      selected_option_ids: answers[q.id] || [],
    }))

    submitMutation.mutate(submitAnswers)
    setShowSubmitDialog(false)
  }, [paper, questions, answers, submitMutation])

  const handleTimeUp = useCallback(() => {
    handleSubmit()
  }, [handleSubmit])

  const answeredCount = Object.keys(answers).filter(
    (key) => answers[key].length > 0,
  ).length

  const unansweredCount = totalQuestions - answeredCount

  const handleSubmitRequest = useCallback(() => {
    if (unansweredCount > 0 && !unansweredSubmitConfirmed) {
      setShowSubmitDialog(true)
      return
    }

    handleSubmit()
  }, [handleSubmit, unansweredCount, unansweredSubmitConfirmed])

  if (paperQuery.isLoading) {
    return <LoadingSkeleton />
  }

  if (!paper) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <div className="rounded-full bg-muted p-4">
          <AlertTriangle className="h-12 w-12 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">无法加载试卷</h3>
        <p className="text-muted-foreground">试卷可能不存在或您没有访问权限</p>
        <Button variant="outline" onClick={() => navigate({ to: "/my-exams" })}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回考试列表
        </Button>
      </div>
    )
  }

  if (submitted && result) {
    return (
      <div className="container mx-auto py-8">
        <Button
          variant="ghost"
          onClick={() => navigate({ to: "/my-exams" })}
          className="mb-6"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回考试列表
        </Button>
        <ResultCard result={result} />
      </div>
    )
  }

  const currentQ = questions[currentQuestion]

  return (
    <div className="container mx-auto py-6 max-w-4xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: "/my-exams" })}
            className="mb-2 -ml-2 text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="mr-1 h-4 w-4" />
            返回
          </Button>
          <h1 className="text-2xl font-bold tracking-tight">
            {paper.exam_name}
          </h1>
          <p className="text-muted-foreground flex items-center gap-2 mt-1">
            <BookOpen className="h-4 w-4" />共 {totalQuestions} 题，及格分{" "}
            {paper.pass_score} 分
          </p>
        </div>
        <Timer totalMinutes={paper.duration_minutes} onTimeUp={handleTimeUp} />
      </div>

      {/* Progress */}
      <Card className="mb-6">
        <CardContent className="py-4">
          <div className="flex items-center justify-between text-sm mb-3">
            <div className="flex items-center gap-4">
              <span className="text-muted-foreground">
                已答{" "}
                <span className="font-semibold text-foreground">
                  {answeredCount}
                </span>{" "}
                / {totalQuestions} 题
              </span>
              {unansweredCount > 0 && (
                <span className="text-amber-600 dark:text-amber-400">
                  还剩 {unansweredCount} 题未答
                </span>
              )}
            </div>
            <span className="text-muted-foreground">
              第 {currentQuestion + 1} / {totalQuestions} 题
            </span>
          </div>
          <Progress
            value={(answeredCount / totalQuestions) * 100}
            className="h-2"
          />
        </CardContent>
      </Card>

      {/* Question */}
      {currentQ && (
        <QuestionCard
          question={currentQ}
          index={currentQuestion}
          selectedOptions={answers[currentQ.id] || []}
          onSelectionChange={(optionIds) =>
            handleSelectionChange(currentQ.id, optionIds)
          }
        />
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between mt-6">
        <Button
          variant="outline"
          disabled={currentQuestion === 0}
          onClick={() => setCurrentQuestion((prev) => prev - 1)}
          className="transition-all"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          上一题
        </Button>

        <div className="flex gap-2">
          {currentQuestion < totalQuestions - 1 ? (
            <Button
              onClick={() => setCurrentQuestion((prev) => prev + 1)}
              className="transition-all"
            >
              下一题
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <Button
              onClick={handleSubmitRequest}
              disabled={submitMutation.isPending || !attemptId}
              className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 shadow-md transition-all"
            >
              {submitMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Send className="mr-2 h-4 w-4" />
              )}
              提交答卷
            </Button>
          )}
        </div>
      </div>

      {/* Question navigation dots */}
      <Card className="mt-6">
        <CardContent className="py-4">
          <div className="flex flex-wrap gap-2 justify-center">
            {questions.map((q, index) => (
              <button
                key={q.id}
                onClick={() => setCurrentQuestion(index)}
                className={`relative w-10 h-10 rounded-lg text-sm font-medium transition-all duration-200 ${
                  index === currentQuestion
                    ? "bg-primary text-primary-foreground shadow-md scale-110"
                    : answers[q.id]?.length > 0
                      ? "bg-emerald-100 text-emerald-800 hover:bg-emerald-200 dark:bg-emerald-900/50 dark:text-emerald-300"
                      : "bg-muted text-muted-foreground hover:bg-muted/80 hover:scale-105"
                }`}
              >
                {index + 1}
                {answers[q.id]?.length > 0 && index !== currentQuestion && (
                  <CheckCircle2 className="absolute -top-1 -right-1 h-3.5 w-3.5 text-emerald-600" />
                )}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Submit confirmation dialog */}
      <AlertDialog open={showSubmitDialog} onOpenChange={setShowSubmitDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认提交答卷</AlertDialogTitle>
            <AlertDialogDescription>
              您还有{" "}
              <span className="font-semibold text-foreground">
                {unansweredCount}
              </span>{" "}
              道题未作答，确定要提交吗？
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>继续答题</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setUnansweredSubmitConfirmed(true)
                handleSubmit()
              }}
            >
              确认提交
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
