/**
 * Question Bank Tool — for all users to browse and download exam papers
 */

import { BookOpen } from "lucide-react"
import { registerTool } from "@/tools/registry"
import { QuestionBankPage } from "./components/QuestionBankPage"

registerTool({
  name: "question_bank",
  group: "exam",
  route: {
    path: "/question-bank",
    title: "试题库",
    component: QuestionBankPage,
  },
  navigation: {
    title: "试题库",
    icon: BookOpen,
    path: "/question-bank",
    requiresSuperuser: false,
  },
})

export { QuestionBankPage }
