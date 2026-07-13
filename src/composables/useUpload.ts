import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useUpload() {
  const uploading = ref(false)
  const uploadProgress = ref(0)

  async function upload(file: File, uploadFn: (file: File) => Promise<any>) {
    uploading.value = true
    uploadProgress.value = 0
    try {
      const interval = setInterval(() => {
        uploadProgress.value = Math.min(uploadProgress.value + 10, 90)
      }, 200)
      const result = await uploadFn(file)
      clearInterval(interval)
      uploadProgress.value = 100
      ElMessage.success('上传成功')
      return result
    } catch (e) {
      ElMessage.error('上传失败')
      throw e
    } finally {
      uploading.value = false
      uploadProgress.value = 0
    }
  }

  return { uploading, uploadProgress, upload }
}
