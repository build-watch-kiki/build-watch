import { cutString } from '../utils/string.ts'
import type {
  DetectionBBoxCenter,
  Snapshot,
  SnapshotDetection
} from '../types/snapshots.ts'

export function formatSnapshotDate(date: Date): string {
  const d = new Date(date)
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')
  return `${day}.${month}.${year} ${hours}:${minutes}:${seconds}`
}

export function getObjectWord(count: number): string {
  if (count % 10 === 1 && count % 100 !== 11) {
    return 'объект'
  }
  if (
    count % 10 >= 2 &&
    count % 10 <= 4 &&
    (count % 100 < 10 || count % 100 >= 20)
  ) {
    return 'объекта'
  }
  return 'объектов'
}

export function getSnapshotRowText(snapshot: Snapshot): string {
  const raw = snapshot.capturedAt || snapshot.createdAt
  const dateStr = formatSnapshotDate(new Date(raw))
  const count = snapshot.detections.length
  if (count === 0) {
    return `Снимок ${dateStr} — объекты не распознаны`
  }
  return `Снимок ${dateStr} — ${count} ${getObjectWord(count)}`
}

export interface DetectionStat {
  techniqueId: number
  objectClass: string
  count: number
  colors: string[]
}

export function getDetectionStats(
  detections: SnapshotDetection[]
): DetectionStat[] {
  const map = new Map<number, DetectionStat>()
  for (const d of detections) {
    const key = d.technique.id
    const stat = map.get(key) ?? {
      techniqueId: key,
      objectClass: d.technique.nameRu,
      count: 0,
      colors: []
    }
    stat.count += 1
    const color = getDetectionColor(d)
    if (!stat.colors.includes(color)) stat.colors.push(color)
    map.set(key, stat)
  }
  return Array.from(map.values()).sort((a, b) => b.count - a.count)
}

const classColors: Record<string, string> = {
  Экскаватор: '#C27803',
  Самосвал: '#2563EB',
  Автокран: '#7C3AED',
  Бетононасос: '#0F766E',
  'Башенный кран': '#BE185D',
  Автовышка: '#0369A1'
}
const fallbackColors = Object.values(classColors)

function normalizeHex(color: unknown): string | null {
  if (typeof color !== 'string') return null
  const trimmed = color.trim()
  return /^#[0-9a-f]{6}$/i.test(trimmed) ? trimmed.toUpperCase() : null
}

export function getDetectionColor(detection: SnapshotDetection): string {
  const serverColor =
    normalizeHex(detection.technique.color) ?? normalizeHex(detection.color)
  if (serverColor) return serverColor
  const name = detection.technique.nameRu
  const known = Object.hasOwn(classColors, name) ? classColors[name] : undefined
  if (known) return known
  let hash = 0
  for (const char of name) hash = (hash * 31 + char.charCodeAt(0)) >>> 0
  return fallbackColors[hash % fallbackColors.length]!
}

export function getDetectionLabelColor(color: string): string {
  const channels = [1, 3, 5].map((start) => {
    const value = parseInt(color.slice(start, start + 2), 16) / 255
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
  })
  const luminance =
    channels[0]! * 0.2126 + channels[1]! * 0.7152 + channels[2]! * 0.0722
  return luminance > 0.179 ? '#000000' : '#FFFFFF'
}

export function cutFileName(name: string, size: number): string {
  if (!name) return ''
  if (name.length <= size) return name
  const dot = name.lastIndexOf('.')
  if (dot <= 0) {
    return cutString(name, size)
  }
  const ext = name.slice(dot)
  const base = name.slice(0, dot)
  const available = size - ext.length
  if (available <= 0) {
    return cutString(name, size)
  }
  if (base.length <= available) {
    return name
  }
  const cutBase = cutString(base, available)
  return cutBase + ext
}

export function formatConfidence(detection: number): string {
  const percent = detection > 1 ? detection : detection * 100
  return `${percent.toFixed(2)}%`
}

export function getDetectionsAvg(detections: SnapshotDetection[]): string {
  if (detections.length === 0) return '—'
  const sum = detections.reduce((acc, d) => {
    const v = d.confidence.detection
    return acc + (v > 1 ? v : v * 100)
  }, 0)
  return `${(sum / detections.length).toFixed(2)}%`
}

export async function downloadSnapshotFile(
  snapshot: Pick<Snapshot, 'url' | 'name'>
): Promise<void> {
  try {
    const response = await fetch(snapshot.url)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const blob = await response.blob()
    const objectUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = objectUrl
    a.download = snapshot.name
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
  } catch {
    window.open(snapshot.url, '_blank', 'noopener')
  }
}

export function getBBoxStyle(
  bbox: DetectionBBoxCenter
): Record<string, string> {
  const values = [bbox.xCenterNorm, bbox.yCenterNorm, bbox.wNorm, bbox.hNorm]
  if (
    !values.every(
      (value) => typeof value === 'number' && Number.isFinite(value)
    )
  ) {
    return { display: 'none' }
  }
  const [xCenter, yCenter, width, height] = values as number[]
  if (width <= 0 || height <= 0) return { display: 'none' }
  return {
    left: `${(xCenter - width / 2) * 100}%`,
    top: `${(yCenter - height / 2) * 100}%`,
    width: `${width * 100}%`,
    height: `${height * 100}%`
  }
}

export function getBoxStyle(
  detection: SnapshotDetection,
  naturalWidth: number,
  naturalHeight: number
): Record<string, string> {
  const bbox = detection.bbox
  const normalized = getBBoxStyle(bbox)
  if (normalized.display !== 'none') return normalized

  const pixelValues = [bbox.xCenter, bbox.yCenter, bbox.w, bbox.h]
  if (
    !pixelValues.every(
      (value) => typeof value === 'number' && Number.isFinite(value)
    )
  ) {
    return { display: 'none' }
  }
  const [xCenter, yCenter, width, height] = pixelValues as number[]
  if (width <= 0 || height <= 0) return { display: 'none' }
  if (!naturalWidth || !naturalHeight) {
    return {
      left: `${xCenter - width / 2}px`,
      top: `${yCenter - height / 2}px`,
      width: `${width}px`,
      height: `${height}px`
    }
  }
  return {
    left: `${((xCenter - width / 2) / naturalWidth) * 100}%`,
    top: `${((yCenter - height / 2) / naturalHeight) * 100}%`,
    width: `${(width / naturalWidth) * 100}%`,
    height: `${(height / naturalHeight) * 100}%`
  }
}
