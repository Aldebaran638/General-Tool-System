import { createFileRoute } from "@tanstack/react-router"
import { QuestionBankSetDetailPage } from "@/tools/exam/question_bank_management/components/QuestionBankSetDetailPage"

export const Route = createFileRoute(
  "/_layout/question-bank-management/$setId",
)({
  component: QuestionBankSetDetailPage,
  head: () => ({
    meta: [{ title: "题库详情" }],
  }),
})
