/** Types for the system dashboard tool module */

export interface QuestionTypeCount {
  question_type: string
  count: number
}

export interface DeviceTypeCount {
  device_type: string
  count: number
}

export interface SystemDashboardStats {
  exam_count: number
  total_participation: number
  overall_pass_rate: number
  question_count: number
  paper_count: number
  question_type_distribution: QuestionTypeCount[]
  device_type_distribution: DeviceTypeCount[]
}
