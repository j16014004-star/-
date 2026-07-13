export interface CareerPlanParams {
  education: string
  skills: string[]
  experience: string
  projects: {
    name: string
    description: string
    role: string
  }[]
}