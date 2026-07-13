export interface ResumeUploadParams {
  file: File
  title?: string
}

export interface ResumeAnalyzeParams {
  resume_id: number
}

export interface ResumeOptimizeParams {
  resume_id: number
  target_position?: string
  requirements?: string
}