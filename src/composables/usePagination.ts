import { ref, computed } from 'vue'

export function usePagination(defaultPageSize = 10) {
  const page = ref(1)
  const pageSize = ref(defaultPageSize)
  const total = ref(0)

  const pagination = computed(() => ({
    page: page.value,
    page_size: pageSize.value,
    total: total.value,
  }))

  function onPageChange(p: number) { page.value = p }
  function onSizeChange(s: number) { pageSize.value = s; page.value = 1 }

  return { page, pageSize, total, pagination, onPageChange, onSizeChange }
}
