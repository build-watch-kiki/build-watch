import type { DateTimeString } from '@/types/api.ts'

export interface DetectionBBoxCenter {
  format: 'xywh_center'
  xCenter: number | null
  yCenter: number | null
  w: number | null
  h: number | null
  xCenterNorm: number | null
  yCenterNorm: number | null
  wNorm: number | null
  hNorm: number | null
}

export interface SnapshotDetectionConfidence {
  detection: number
}

export interface SnapshotDetection {
  objectId: number
  color?: string | null
  technique: {
    id: number
    name: string
    nameRu: string
    color: string | null
  }
  confidence: SnapshotDetectionConfidence
  bbox: DetectionBBoxCenter
}

export interface Model {
  name: string
  version: string
  weights: string
}

export interface Snapshot {
  id: number
  projectId: number
  name: string
  url: string
  detections: SnapshotDetection[]
  capturedAt: DateTimeString
  createdAt: DateTimeString
  width: number
  height: number
  format: string
  isProcessed: boolean
  processingStatus: 'pending' | 'succeeded' | 'failed'
  model: Model | null
  demo?: boolean
}
