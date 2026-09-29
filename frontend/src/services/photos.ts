import { api } from '@/store/api'
import { addMockPhotoFromFile, isMockProject } from '@/mock/index.ts'
import type { PhotoPage } from '@/types/photos'
import type { PhotoResponse } from '@/types/photos'

export const MAX_UPLOAD_BATCH = 20
export const UPLOAD_CONCURRENCY = 3

export type PhotoUploadStatus = 'queued' | 'uploading' | 'accepted' | 'error'

export interface PhotoUploadEntry {
  file: File
  /** Дата снимка YYYY-MM-DD, null — не указана. */
  capturedAt: string | null
}

export interface PhotoUploadItem {
  key: string
  file: File
  capturedAt: string | null
  status: PhotoUploadStatus
  id?: number
  error?: string
}

/** Дата из date-инпута → полночь UTC ISO. */
export function toCapturedAtIso(date: string): string {
  return `${date}T00:00:00.000Z`
}

export async function fetchPhotos(
  projectId: number,
  page: number,
  pageSize = 15
): Promise<PhotoPage> {
  const response = await api.get<PhotoPage>(`/projects/${projectId}/photos`, {
    params: { page, pageSize }
  })
  return response.data
}

export async function uploadPhoto(
  projectId: number,
  file: File,
  capturedAt?: string | null
): Promise<number> {
  if (isMockProject(projectId)) {
    return addMockPhotoFromFile(file, capturedAt).id
  }
  const body = new FormData()
  body.append('file', file)
  if (capturedAt) {
    body.append('capturedAt', toCapturedAtIso(capturedAt))
  }
  // Axios/browser supplies the multipart boundary. Do not force Content-Type.
  const response = await api.post<{ id: number }>(
    `/projects/${projectId}/photos`,
    body
  )
  return response.data.id
}

export async function fetchPhoto(
  projectId: number,
  photoId: number
): Promise<PhotoResponse> {
  const response = await api.get<PhotoResponse>(
    `/projects/${projectId}/photos/${photoId}`
  )
  return response.data
}

function errorMessage(error: unknown): string {
  const detail = (error as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail
  if (typeof detail === 'string') return detail
  return error instanceof Error ? error.message : 'Не удалось загрузить файл'
}

export async function uploadPhotoBatch(
  projectId: number,
  entries: PhotoUploadEntry[],
  onProgress?: (items: PhotoUploadItem[]) => void,
  concurrency = UPLOAD_CONCURRENCY
): Promise<PhotoUploadItem[]> {
  const items: PhotoUploadItem[] = entries.map((entry, index) => ({
    key: `${entry.file.name}:${entry.file.size}:${entry.file.lastModified}:${index}`,
    file: entry.file,
    capturedAt: entry.capturedAt,
    status: 'queued'
  }))
  let cursor = 0
  const publish = () => onProgress?.(items.map((item) => ({ ...item })))

  async function worker() {
    while (cursor < items.length) {
      const index = cursor
      cursor += 1
      const item = items[index]!
      item.status = 'uploading'
      publish()
      try {
        item.id = await uploadPhoto(projectId, item.file, item.capturedAt)
        item.status = 'accepted'
      } catch (error) {
        item.status = 'error'
        item.error = errorMessage(error)
      }
      publish()
    }
  }

  const workerCount = Math.min(Math.max(1, concurrency), items.length)
  await Promise.all(Array.from({ length: workerCount }, () => worker()))
  return items
}
