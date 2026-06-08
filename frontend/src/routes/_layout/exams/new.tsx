import { createFileRoute } from "@tanstack/react-router"
import { NewExamPage } from "@/tools/exam/exam_management/components/NewExamPage"

export const Route = createFileRoute("/_layout/exams/new")({
  component: NewExamPage,
  head: () => ({
    meta: [{ title: "新建考试" }],
  }),
})
