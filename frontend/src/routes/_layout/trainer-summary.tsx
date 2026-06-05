import { createFileRoute, redirect } from "@tanstack/react-router"

import { UsersService } from "@/client"
import { TrainerSummaryPage } from "@/tools/workbench/trainer_summary/components/TrainerSummaryPage"

export const Route = createFileRoute("/_layout/trainer-summary")({
  component: TrainerSummaryPage,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (!user.is_superuser) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "培训讲师汇总 - 考试管理系统" }],
  }),
})
