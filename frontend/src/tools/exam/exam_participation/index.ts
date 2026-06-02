/**
 * Exam Participation Tool — for regular users
 */

import { GraduationCap } from "lucide-react"
import { registerTool } from "@/tools/registry"
import { ExamParticipationPage } from "./components/ExamParticipationPage"

registerTool({
  name: "exam_participation",
  group: "exam",
  route: {
    path: "/my-exams",
    title: "我的考试",
    component: ExamParticipationPage,
  },
  navigation: {
    title: "我的考试",
    icon: GraduationCap,
    path: "/my-exams",
    requiresSuperuser: false,
  },
})

export { ExamParticipationPage }
