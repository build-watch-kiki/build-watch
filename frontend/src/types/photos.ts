export interface PhotoResponse {
  id: number
  name: string
  url: string
  capturedAt: string | null
  createdAt: string
  isProcessed: boolean
  processingStatus?: 'pending' | 'succeeded' | 'failed'
  width: number | null
  height: number | null
  format?: string | null
  model?: {
    name: string
    version: string
    weights: string
  } | null
  detections: Array<{
    objectId: number
    classId: number
    className: string
    technique?: {
      id: number
      name: string
      nameRu: string
      color: string
    } | null
    color?: string | null
    confidence: {
      detection: number
      activity?: number | null
      activityState?: string | null
    }
    bbox: {
      format?: 'xywh_center'
      xCenterNorm: number | null
      yCenterNorm: number | null
      wNorm: number | null
      hNorm: number | null
    }
  }>
}

export interface PhotoPage {
  items: PhotoResponse[]
  metadata: {
    total: number
    page: number
    pageSize: number
    totalPages?: number
  }
}
