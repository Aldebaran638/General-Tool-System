import { FolderOpen } from "lucide-react"
import { registerTool } from "@/tools/registry"
import { ExamCategoryManagementPage } from "./components/ExamCategoryManagementPage"

registerTool({
  name: "category_management",
  group: "exam",
  route: {
    path: "/exam-categories",
    title: "试卷分类",
    component: ExamCategoryManagementPage,
  },
  navigation: {
    title: "试卷分类",
    icon: FolderOpen,
    path: "/exam-categories",
    requiresSuperuser: true,
  },
})

export { ExamCategoryManagementPage }
