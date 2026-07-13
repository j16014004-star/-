import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Resume, ResumeAnalysis } from '@/types'

export const useResumeStore = defineStore('resume', () => {
  const resumes = ref<Resume[]>([])
  const currentResume = ref<Resume | null>(null)
  const loading = ref(false)
  const analyzing = ref(false)

  function setResumes(list: Resume[]) {
    resumes.value = list
  }

  function setCurrent(resume: Resume | null) {
    currentResume.value = resume
  }

  function addResume(resume: Resume) {
    resumes.value.unshift(resume)
  }

  function removeResume(id: number) {
    resumes.value = resumes.value.filter(r => r.id !== id)
  }

  function updateAnalysis(id: number, analysis: ResumeAnalysis) {
    const resume = resumes.value.find(r => r.id === id)
    if (resume) {
      resume.analysis = analysis
      resume.score = analysis.score
      resume.status = 'completed'
    }
    if (currentResume.value?.id === id) {
      currentResume.value.analysis = analysis
      currentResume.value.score = analysis.score
      currentResume.value.status = 'completed'
    }
  }

  return {
    resumes, currentResume, loading, analyzing,
    setResumes, setCurrent, addResume, removeResume, updateAnalysis
  }
})
