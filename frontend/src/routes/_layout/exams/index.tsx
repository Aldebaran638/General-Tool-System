import { createFileRoute } from "@tanstack/react-router"
import { ExamListPage } from "@/tools/exam/exam_management/components/ExamListPage"

export const Route = createFileRoute("/_layout/exams/")({
  component: ExamListPage,
  head: () => ({
    meta: [{ title: "考试管理" }],
  }),
})
