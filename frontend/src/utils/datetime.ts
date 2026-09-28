export function displayDate(
  date: string | null | undefined,
  minutes = false
): string {
  if (!date) return '-'

  const value = new Date(date)

  if (Number.isNaN(value.getTime())) {
    return '-'
  }

  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    ...(minutes
      ? {
          hour: '2-digit',
          minute: '2-digit'
        }
      : {})
  }).format(value)
}
