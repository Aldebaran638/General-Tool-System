/**
 * Trainer Summary Tool Module
 *
 * Displays a table of all trainers and their associated exam information.
 * Only visible to superusers.
 *
 * Self-registers with the global tool registry on import.
 */

import { GraduationCap } from "lucide-react"

import { registerTool } from "@/tools/registry"
import { TrainerSummaryPage } from "./components/TrainerSummaryPage"

registerTool({
  name: "trainer_summary",
  group: "workbench",
  route: {
    path: "/trainer-summary",
    title: "培训讲师汇总 - 考试管理系统",
    component: TrainerSummaryPage,
  },
  navigation: {
    title: "培训讲师汇总",
    icon: GraduationCap,
    path: "/trainer-summary",
    requiresSuperuser: true,
  },
})

export { TrainerSummaryPage }
export * from "./api"
