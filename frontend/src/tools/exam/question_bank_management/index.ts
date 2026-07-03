import { BookOpen } from "lucide-react"
import { registerTool } from "@/tools/registry"
import { QuestionBankManagementPage } from "./components/QuestionBankManagementPage"

registerTool({
  name: "question_bank_management",
  group: "exam",
  route: {
    path: "/question-bank-management",
    title: "题库管理",
    component: QuestionBankManagementPage,
  },
  navigation: {
    title: "题库管理",
    icon: BookOpen,
    path: "/question-bank-management",
    requiresExamAdmin: true,
  },
})

export { QuestionBankManagementPage }
