/**
 * Exam Taking Route — for users to take a specific exam
 */

import { createFileRoute } from "@tanstack/react-router"
import { ExamTakingPage } from "@/tools/exam/exam_participation/components/ExamTakingPage"

export const Route = createFileRoute("/_layout/my-exams/$examId")({
  component: ExamTakingPage,
  head: () => ({
    meta: [
      {
        title: "参加考试 - 通用工具系统",
      },
    ],
  }),
})
