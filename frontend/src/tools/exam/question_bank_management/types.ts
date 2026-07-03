/** Types for question bank management module */

export type ImportMode = "append" | "overwrite"

export interface QuestionBankOption {
  id: string
  question_id: string
  option_key: string
  option_text: string
  is_correct: boolean
  sort_no: number
}

export interface QuestionBankOptionCreate {
  option_key: string
  option_text: string
  is_correct?: boolean
  sort_no?: number
}

export interface QuestionBankQuestion {
  id: string
  set_id: string
  question_type: "SINGLE_CHOICE" | "MULTIPLE_CHOICE" | "TRUE_FALSE"
  stem: string
  score: number
  difficulty: string
  sort_no: number
  analysis: string | null
  options: QuestionBankOption[]
}

export interface QuestionBankQuestionCreate {
  question_type: "SINGLE_CHOICE" | "MULTIPLE_CHOICE" | "TRUE_FALSE"
  stem: string
  score: number
  difficulty?: string
  sort_no?: number
  analysis?: string | null
  options: QuestionBankOptionCreate[]
}

export interface QuestionBankSet {
  id: string
  name: string
  description: string | null
  category_id: number | null
  created_by: string
  created_at: string | null
  updated_at: string | null
}

export interface QuestionBankSetCreate {
  name: string
  description?: string
  category_id?: number | null
}

export interface QuestionBankSetsResponse {
  data: QuestionBankSet[]
  count: number
}

export interface QuestionBankSetDetail {
  set: QuestionBankSet
  questions: QuestionBankQuestion[]
}

export interface ImportQuestionBankRequest {
  bank_set_id: string
  mode: ImportMode
}
