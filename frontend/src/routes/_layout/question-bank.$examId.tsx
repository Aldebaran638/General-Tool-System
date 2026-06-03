/**
 * Question Bank Preview Route — online preview of exam paper
 */

import { createFileRoute } from "@tanstack/react-router"
import { QuestionBankPreviewPage } from "@/tools/exam/question_bank/components/QuestionBankPreviewPage"

export const Route = createFileRoute("/_layout/question-bank/$examId")({
  component: QuestionBankPreviewPage,
  head: () => ({
    meta: [
      {
        title: "试卷预览 - 通用工具系统",
      },
    ],
  }),
})
