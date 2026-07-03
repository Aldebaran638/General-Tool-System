import { createFileRoute } from "@tanstack/react-router"
import { QuestionBankManagementPage } from "@/tools/exam/question_bank_management"

export const Route = createFileRoute("/_layout/question-bank-management/")({
  component: QuestionBankManagementPage,
  head: () => ({
    meta: [{ title: "题库管理" }],
  }),
})
