import type { DateTimeString } from '../types/api.ts'
import type { PhotoResponse } from '../types/photos.ts'
import type { Snapshot } from '../types/snapshots.ts'

export const MAX_PHOTO_SIZE = 20 * 1024 * 1024

export const ACCEPTED_PHOTO_TYPES = ['image/jpeg', 'image/png'] as const

export const ACCEPTED_PHOTO_ACCEPT = ACCEPTED_PHOTO_TYPES.join(',')

export function validatePhoto(
  file: Pick<File, 'size' | 'type'>
): string | null {
  if (!(ACCEPTED_PHOTO_TYPES as readonly string[]).includes(file.type))
    return 'Выберите JPEG или PNG.'
  if (!file.size) return 'Файл пуст.'
  if (file.size > MAX_PHOTO_SIZE)
    return 'Максимальный размер фотографии — 20 МиБ.'
  return null
}

export function adaptPhoto(photo: PhotoResponse, projectId: number): Snapshot {
  return {
    id: photo.id,
    projectId,
    name: photo.name,
    url: photo.url,
    capturedAt: (photo.capturedAt || photo.createdAt) as DateTimeString,
    createdAt: photo.createdAt as DateTimeString,
    width: photo.width ?? 0,
    height: photo.height ?? 0,
    format: photo.format?.toLowerCase() ?? '',
    isProcessed: photo.isProcessed,
    processingStatus:
      photo.processingStatus ?? (photo.isProcessed ? 'succeeded' : 'pending'),
    model: photo.model ?? null,
    demo: false,
    detections: photo.detections.map((detection) => ({
      objectId: detection.objectId,
      color: detection.color,
      technique: detection.technique
        ? {
            id: detection.technique.id,
            name: detection.technique.name,
            nameRu: detection.technique.nameRu,
            color: detection.technique.color ?? detection.color ?? null
          }
        : {
            id: -(Math.abs(detection.classId) + 1),
            name: detection.className,
            nameRu: detection.className,
            color: detection.color ?? null
          },
      confidence: { detection: detection.confidence.detection },
      bbox: {
        format: 'xywh_center',
        xCenter: null,
        yCenter: null,
        w: null,
        h: null,
        xCenterNorm: detection.bbox.xCenterNorm,
        yCenterNorm: detection.bbox.yCenterNorm,
        wNorm: detection.bbox.wNorm,
        hNorm: detection.bbox.hNorm
      }
    }))
  }
}
