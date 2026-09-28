import type { DateString, DateTimeString } from '@/types/api.ts'
import type {
  DailyProgressDetail,
  DailyProgressSummary,
  ProgressDetailMessage,
  ProgressStatus,
  ProgressTechniquePlanFact
} from '@/types/progress.ts'
import { MOCK_PHOTOS } from './photos.ts'
import type { PhotoResponse } from '@/types/photos.ts'

const MOCK_DATES: DateString[] = [
  '2026-09-20',
  '2026-09-21',
  '2026-09-22',
  '2026-09-23',
  '2026-09-24',
  '2026-09-25',
  '2026-09-26',
  '2026-09-27'
]

const MOCK_STATUSES: ProgressStatus[] = [
  'on_track',
  'on_track',
  'behind',
  'on_track',
  'ahead',
  'unknown',
  'on_track',
  'behind'
]

const STAGE_PREP = { id: 1, name: 'Подготовка основания', score: 0.93 }
const STAGE_ASPHALT = { id: 4, name: 'Укладка асфальта', score: 0.88 }

function techniqueItem(
  id: number,
  name: string,
  plan: number,
  fact: number
): ProgressTechniquePlanFact {
  const delta = fact - plan
  return {
    id,
    name,
    plan,
    fact,
    delta,
    status:
      delta === 0
        ? 'on_plan'
        : fact === 0
          ? 'missing'
          : plan === 0
            ? 'unexpected'
            : 'quantity_mismatch'
  }
}

function dayTechniques(date: DateString): ProgressTechniquePlanFact[] {
  switch (date) {
    case '2026-09-22':
    case '2026-09-27':
      return [
        techniqueItem(1, 'Экскаватор', 2, 2),
        techniqueItem(2, 'Самосвал', 3, 2),
        techniqueItem(3, 'Каток', 1, 1)
      ]
    case '2026-09-24':
      return [
        techniqueItem(4, 'Автогрейдер', 1, 1),
        techniqueItem(5, 'Автокран', 1, 1)
      ]
    case '2026-09-25':
      return []
    default:
      return [
        techniqueItem(1, 'Экскаватор', 2, 2),
        techniqueItem(2, 'Самосвал', 3, 3),
        techniqueItem(3, 'Каток', 1, 1)
      ]
  }
}

function dayEvidence(date: DateString): PhotoResponse[] {
  return MOCK_PHOTOS.filter((photo) =>
    (photo.capturedAt ?? '').startsWith(date)
  )
}

function summaryFor(
  date: DateString,
  status: ProgressStatus,
  isFinal: boolean
): DailyProgressSummary {
  const behind = status === 'behind'
  const ahead = status === 'ahead'
  const unknown = status === 'unknown'
  return {
    date,
    isFinal,
    status,
    deviationDays: unknown ? null : ahead ? -1 : behind ? 2 : 0,
    techniqueDeviationCount: behind ? 1 : 0,
    message: {
      code: behind
        ? 'stage_timing_deviation'
        : ahead
          ? 'stage_timing_deviation'
          : unknown
            ? 'insufficient_data'
            : 'on_track',
      severity: behind ? 'warning' : 'info',
      text: behind
        ? 'Этап отстаёт от календарного плана'
        : ahead
          ? 'Следующий этап начался раньше'
          : unknown
            ? 'Недостаточно данных для оценки'
            : 'Работы идут по плану'
    },
    stages: {
      previous: null,
      current: unknown ? null : { ...STAGE_PREP },
      next: unknown ? null : { ...STAGE_ASPHALT }
    },
    quality: unknown ? 'insufficient' : 'high'
  }
}

export function createMockProgressHistory(): DailyProgressSummary[] {
  return MOCK_DATES.map((date, index) =>
    summaryFor(date, MOCK_STATUSES[index]!, index < MOCK_DATES.length - 1)
  )
}

export function createMockProgressDetail(
  date: string
): DailyProgressDetail | null {
  const index = (MOCK_DATES as string[]).indexOf(date)
  if (index === -1) return null
  const day = MOCK_DATES[index]!
  const status = MOCK_STATUSES[index]!
  const summary = summaryFor(day, status, true)
  const unknown = status === 'unknown'
  const behind = status === 'behind'
  const ahead = status === 'ahead'
  const items = dayTechniques(day)
  const evidence = dayEvidence(day)
  const stageRefId = 1
  const messages: ProgressDetailMessage[] = []
  if (behind || ahead) {
    messages.push({
      code: 'stage_timing_deviation',
      severity: 'warning',
      text: behind
        ? 'Этап отстаёт от календарного плана'
        : 'Следующий этап начался раньше',
      category: 'schedule',
      stageId: stageRefId,
      techniqueId: null,
      evidencePhotoIds: evidence.map((photo) => photo.id)
    })
  }
  for (const item of items) {
    if (item.status === 'on_plan') continue
    messages.push({
      code: 'quantity_mismatch',
      severity: 'warning',
      text: `${item.name}: количество ниже плана`,
      category: 'technique',
      stageId: stageRefId,
      techniqueId: item.id,
      evidencePhotoIds: evidence.slice(0, 1).map((photo) => photo.id)
    })
  }
  if (unknown) {
    messages.push({
      code: 'low_data_quality',
      severity: 'warning',
      text: 'Нет пригодных наблюдений для надёжного сопоставления с планом.',
      category: 'quality',
      stageId: null,
      techniqueId: null,
      evidencePhotoIds: []
    })
  }
  return {
    ...summary,
    techniques: { stageId: unknown ? null : stageRefId, items },
    messages,
    quality: {
      level: unknown ? 'insufficient' : 'high',
      observations: unknown
        ? { total: 0, usable: 0 }
        : { total: 30 + index * 2, usable: 27 + index * 2 },
      coverage: unknown ? 0 : 0.93,
      agreement: unknown ? 0 : 0.89,
      reasons: unknown ? ['no_observations'] : []
    },
    evidence: evidence.map((photo) => ({
      id: photo.id,
      url: photo.url,
      capturedAt: (photo.capturedAt ?? photo.createdAt) as DateTimeString,
      reasonCodes: [],
      detections: photo.detections.map((detection) => ({
        objectId: detection.objectId,
        classId: detection.classId,
        className: detection.className,
        color: detection.color ?? detection.technique?.color ?? '#2563EB',
        technique: detection.technique
          ? {
              id: detection.technique.id,
              name: detection.technique.name,
              nameRu: detection.technique.nameRu,
              color: detection.technique.color
            }
          : null,
        confidence: { detection: detection.confidence.detection },
        bbox: {
          format: 'xywh_center',
          xCenterNorm: detection.bbox.xCenterNorm,
          yCenterNorm: detection.bbox.yCenterNorm,
          wNorm: detection.bbox.wNorm,
          hNorm: detection.bbox.hNorm
        }
      }))
    }))
  }
}
