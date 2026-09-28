import type { DateString, DateTimeString } from './api'
import type { Snapshot } from './snapshots'

export type ProgressStatus = 'ahead' | 'on_track' | 'behind' | 'unknown'
export type ProgressDataQuality = 'high' | 'medium' | 'low' | 'insufficient'
export type ProgressMessageSeverity = 'info' | 'warning'
export type ProgressMessageCategory =
  'schedule' | 'technique' | 'quality' | 'stage'
export type ProgressTechniqueStatus =
  'on_plan' | 'missing' | 'unexpected' | 'quantity_mismatch'

export interface ProgressMessage {
  code: string
  severity: ProgressMessageSeverity
  text: string
}

export interface ProgressDetailMessage extends ProgressMessage {
  category: ProgressMessageCategory
  stageId: number | null
  techniqueId: number | null
  evidencePhotoIds: number[]
}

export interface ProgressStageMatch {
  id: number
  name: string
  score: number | null
}

export interface ProgressStages {
  previous: ProgressStageMatch | null
  current: ProgressStageMatch | null
  next: ProgressStageMatch | null
}

export interface DailyProgressSummary {
  date: DateString
  isFinal: boolean
  status: ProgressStatus
  deviationDays: number | null
  techniqueDeviationCount: number
  message: ProgressMessage
  stages: ProgressStages
  quality: ProgressDataQuality
}

export interface ProgressTechniquePlanFact {
  id: number | null
  name: string
  plan: number
  fact: number
  delta: number
  status: ProgressTechniqueStatus
}

export interface ProgressTechniques {
  stageId: number | null
  items: ProgressTechniquePlanFact[]
}

export interface ProgressQuality {
  level: ProgressDataQuality
  observations: { total: number; usable: number }
  coverage: number
  agreement: number
  reasons: string[]
}

export interface ProgressEvidenceDetection {
  objectId: number
  classId: number
  className: string
  color: string
  technique: {
    id: number
    name: string
    nameRu: string
    color: string
  } | null
  confidence: { detection: number; activity?: number | null }
  bbox: {
    format: 'xywh_center'
    xCenterNorm: number | null
    yCenterNorm: number | null
    wNorm: number | null
    hNorm: number | null
  }
}

export interface ProgressEvidence {
  id: number
  url: string
  capturedAt: DateTimeString
  reasonCodes: string[]
  detections: ProgressEvidenceDetection[]
}

export interface DailyProgressDetail extends Omit<
  DailyProgressSummary,
  'quality'
> {
  techniques: ProgressTechniques
  messages: ProgressDetailMessage[]
  quality: ProgressQuality
  evidence: ProgressEvidence[]
}

export interface StageActualProgress {
  startDate: DateString
  endDate: DateString
  status: ProgressStatus
  deviationDays: number | null
  techniqueDeviationCount: number
  message: ProgressMessage
}

export interface ProgressListResponse<T> {
  items: T[]
  metadata: { total: number; limit: number | null }
}

export type ProgressCategory = 'all' | 'timing' | 'equipment'

export interface ProgressEquipment {
  techniqueId: number | null
  name: string
  icon: string
  plannedQuantity: number
  actualQuantity: number
  delta: number
  deviationType: ProgressTechniqueStatus | 'none'
}

export interface ProgressDeviation {
  id: string
  code: string
  message: string
  explanation: string
  expected: string
  actual: string
  evidenceIds: number[]
  category: Exclude<ProgressCategory, 'all'>
  categoryLabel: string
  icon: string
}

export interface DashboardDay {
  projectId: number
  date: DateString
  actualStage: string | null
  currentStageScore: number | null
  stages: ProgressStages
  timingStatus: ProgressStatus
  timeDeviationDays: number | null
  observationCount: number
  usableObservationCount: number
  processingCoverage: number
  agreementRate: number | null
  dataQuality: ProgressDataQuality
  dataQualityReasons: string[]
  equipment: ProgressEquipment[]
  evidencePhotos: Snapshot[]
  timingLabel: string
  timingIcon: string
  timingTone: 'success' | 'info' | 'warning' | 'neutral'
  qualityLabel: string
  coveragePercent: number
  agreementPercent: number | null
  deviations: ProgressDeviation[]
  deviationCount: number
  message: ProgressMessage
}

// Demo fixtures remain available for isolated visual development.
export type ProgressTimingStatus = 'on_schedule' | 'early' | 'late' | 'unknown'
export type ProgressWarningCode =
  | 'missing_required_equipment'
  | 'unexpected_equipment'
  | 'quantity_mismatch'
  | 'stage_timing_deviation'
  | 'low_data_quality'
export interface ProgressWarningSource {
  id: string
  code: ProgressWarningCode
  message: string
  explanation: string
  expected: string
  actual: string
  evidenceIds: number[]
}
export interface DailyProgressSource {
  projectId: number
  date: string
  actualStage: string | null
  plannedStage: string
  timingStatus: ProgressTimingStatus
  timeDeviationDays: number | null
  observationCount: number
  usableObservationCount: number
  processingCoverage: number
  agreementRate: number | null
  dataQuality: ProgressDataQuality
  dataQualityReasons: string[]
  equipment: ProgressEquipment[]
  warnings: ProgressWarningSource[]
  evidencePhotos: Snapshot[]
}
