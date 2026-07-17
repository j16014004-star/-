export function resolveMediaUrl(value?: string | null): string {
  const url = String(value || '').trim()
  if (!url) return ''
  if (url.startsWith('/uploads/')) return `/api${url}`
  return url
}

export function withCacheVersion(value: string, version: number): string {
  if (!value || !version) return value
  const separator = value.includes('?') ? '&' : '?'
  return `${value}${separator}v=${version}`
}
