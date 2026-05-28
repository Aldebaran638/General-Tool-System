import { createFileRoute } from "@tanstack/react-router"
import { ExamDetailPage } from "@/tools/exam/exam_management/components/ExamDetailPage"

export const Route = createFileRoute("/_layout/exams/$examId")({
  component: ExamDetailPage,
  head: () => ({
    meta: [{ title: "考试详情" }],
  }),
})
