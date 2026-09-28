import axios from 'axios'

export function getApiErrorDetail(
  error: unknown,
  fallback = 'Неизвестная ошибка'
): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { detail?: unknown } | undefined
    if (data && typeof data.detail === 'string' && data.detail.trim()) {
      return data.detail
    }
    if (error.message) return error.message
    return fallback
  }
  if (error instanceof Error && error.message) return error.message
  return fallback
}
