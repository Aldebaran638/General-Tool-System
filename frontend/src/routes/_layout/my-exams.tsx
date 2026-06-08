/**
 * My Exams Route — for regular users to view their exams
 */

import { createFileRoute, Outlet, useMatches } from "@tanstack/react-router"
import { ExamParticipationPage } from "@/tools/exam/exam_participation/components/ExamParticipationPage"

function MyExamsLayout() {
  const matches = useMatches()
  const isChildRoute = matches.some(
    (m) => m.routeId === "/_layout/my-exams/$examId"
  )

  if (isChildRoute) {
    return <Outlet />
  }

  return <ExamParticipationPage />
}

export const Route = createFileRoute("/_layout/my-exams")({
  component: MyExamsLayout,
  head: () => ({
    meta: [
      {
        title: "我的考试 - 通用工具系统",
      },
    ],
  }),
})
