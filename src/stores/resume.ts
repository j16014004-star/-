import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Resume } from '@/types'

export const useResumeStore = defineStore('resume', () => {
  const resumes = ref<Resume[]>([])
  const currentResume = ref<Resume | null>(null)
  const loading = ref(false)

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

  return {
    resumes, currentResume, loading,
    setResumes, setCurrent, addResume, removeResume
  }
})
