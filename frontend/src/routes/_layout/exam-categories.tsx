import { createFileRoute, redirect } from "@tanstack/react-router"

import { UsersService } from "@/client"
import { ExamCategoryManagementPage } from "@/tools/exam/category_management/components/ExamCategoryManagementPage"

export const Route = createFileRoute("/_layout/exam-categories")({
  component: ExamCategoryManagementPage,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (!user.is_superuser) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "试卷分类 - 考试管理系统" }],
  }),
})
