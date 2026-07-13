export interface InterviewCreateParams {
  position: string
  company?: string
  question_types?: string[]
  question_count?: number
}

export interface InterviewAnswerParams {
  question_id: number
  answer: string
  duration: number
}