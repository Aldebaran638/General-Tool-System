/**
 * Question Bank Route — browse and download exam papers
 */

import { createFileRoute, Outlet, useMatches } from "@tanstack/react-router"
import { QuestionBankPage } from "@/tools/exam/question_bank/components/QuestionBankPage"

function QuestionBankLayout() {
  const matches = useMatches()
  const isChildRoute = matches.some(
    (m) => m.routeId === "/_layout/question-bank/$examId",
  )

  if (isChildRoute) {
    return <Outlet />
  }

  return <QuestionBankPage />
}

export const Route = createFileRoute("/_layout/question-bank")({
  component: QuestionBankLayout,
  head: () => ({
    meta: [
      {
        title: "试题库 - 通用工具系统",
      },
    ],
  }),
})
