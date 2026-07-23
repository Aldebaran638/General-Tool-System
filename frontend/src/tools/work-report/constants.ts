export const SECTION_FIELDS = {
  work_plan: [
    "plan_content",
    "planned_completion_date",
    "expected_result",
    "support_needed",
    "remarks",
  ],
  task_summary: [
    "work_goal",
    "completion_date",
    "progress_description",
    "progress",
    "incomplete_reason",
  ],
  work_review: ["review_module", "review_content"],
} as const

export type SectionKey = keyof typeof SECTION_FIELDS

export const SECTION_LABELS: Record<SectionKey, string> = {
  work_plan: "工作计划",
  task_summary: "任务总结",
  work_review: "工作复盘",
}

export const FIELD_LABELS: Record<string, string> = {
  plan_content: "计划内容",
  planned_completion_date: "计划完成时间",
  expected_result: "预期工作成果",
  support_needed: "所需支持",
  remarks: "备注",
  work_goal: "本周工作目标",
  completion_date: "完成时间",
  progress_description: "当前工作进展情况",
  progress: "当前进度",
  incomplete_reason: "未完成原因分析",
  review_module: "复盘模块",
  review_content: "复盘内容",
}
