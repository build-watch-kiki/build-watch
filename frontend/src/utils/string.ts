export function cutString(value: string | null | undefined, size = 30): string {
  if (value === null || value === undefined) {
    return ''
  }

  const str = String(value)

  if (str.length <= size) {
    return str
  }

  return str.slice(0, size).trimEnd() + '...'
}
