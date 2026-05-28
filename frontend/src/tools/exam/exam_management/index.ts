import { FileText } from "lucide-react"
import { registerTool } from "@/tools/registry"
import { ExamListPage } from "./components/ExamListPage"

registerTool({
  name: "exam_management",
  group: "exam",
  route: {
    path: "/exams",
    title: "考试管理",
    component: ExamListPage,
  },
  navigation: {
    title: "考试管理",
    icon: FileText,
    path: "/exams",
    requiresSuperuser: true,
  },
})

export { ExamListPage }
