import axios from 'axios'

export const api = axios.create({
  baseURL: window.__BUILDWATCH_CONFIG__?.apiBaseUrl || '/api/',
  timeout: 30000
})

const s3Origin = window.__BUILDWATCH_CONFIG__?.s3Origin

function proxyS3Url(value: unknown): unknown {
  if (typeof value !== 'string' || !s3Origin) return value
  try {
    const url = new URL(value)
    if (url.origin !== s3Origin) return value
    return `/s3${url.pathname}${url.search}`
  } catch {
    return value
  }
}

function proxyS3Urls(data: unknown): void {
  if (Array.isArray(data)) {
    data.forEach(proxyS3Urls)
    return
  }
  if (data === null || typeof data !== 'object') return

  const record = data as Record<string, unknown>
  for (const key of ['url', 'original_url', 'originalUrl']) {
    if (key in record) record[key] = proxyS3Url(record[key])
  }
  Object.values(record).forEach(proxyS3Urls)
}

api.interceptors.response.use((response) => {
  proxyS3Urls(response.data)
  return response
})
