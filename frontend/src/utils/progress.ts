import type { DateString } from '../types/api.ts'
import type {
  DailyProgressDetail,
  DailyProgressSummary,
  DashboardDay,
  ProgressCategory,
  ProgressDataQuality,
  ProgressDetailMessage,
  ProgressDeviation,
  ProgressEvidence,
  ProgressStatus,
  ProgressTechniquePlanFact
} from '../types/progress.ts'
import type { Snapshot } from '../types/snapshots.ts'

const timingLabels: Record<ProgressStatus, string> = {
  on_track: 'По плану',
  ahead: 'Опережаем план',
  behind: 'Отстаём от плана',
  unknown: 'Недостаточно данных'
}

const qualityLabels: Record<ProgressDataQuality, string> = {
  high: 'Высокое',
  medium: 'Среднее',
  low: 'Низкое',
  insufficient: 'Недостаточно данных'
}

const reasonLabels: Record<string, string> = {
  no_usable_observations: 'Нет пригодных наблюдений за выбранный день.',
  class_mapping_missing:
    'Распознанные классы техники отсутствуют в справочнике.',
  no_leaf_stages: 'В календарном плане нет конечных этапов для сопоставления.',
  stage_has_no_technique_plan: 'Для этапа не задан план техники.',
  indistinguishable_stage_templates:
    'Состав техники соседних этапов невозможно различить.',
  low_stage_score: 'Уверенность определения этапа ниже допустимого порога.',
  too_few_usable_observations: 'Слишком мало пригодных наблюдений.',
  low_processing_coverage: 'Обработана недостаточная доля снимков.',
  unstable_counts: 'Количество техники нестабильно между наблюдениями.',
  limited_observation_count: 'Количество наблюдений ограничено.',
  partial_processing_coverage: 'Часть снимков ещё не обработана.',
  moderate_count_variance: 'Количество техники различается между снимками.'
}

const deviationIcons: Record<string, string> = {
  stage_ahead: 'mdi-calendar-arrow-left',
  stage_behind: 'mdi-calendar-alert-outline',
  missing_required_equipment: 'mdi-truck-alert-outline',
  unexpected_equipment: 'mdi-truck-plus-outline',
  quantity_mismatch: 'mdi-counter'
}

function toPercent(value: number): number {
  return Math.round(Math.max(0, Math.min(1, value)) * 100)
}

function evidenceToSnapshot(
  evidence: ProgressEvidence,
  projectId: number
): Snapshot {
  return {
    id: evidence.id,
    projectId,
    name: `Подтверждение №${evidence.id}`,
    url: evidence.url,
    capturedAt: evidence.capturedAt,
    createdAt: evidence.capturedAt,
    width: 0,
    height: 0,
    format: 'webp',
    isProcessed: true,
    processingStatus: 'succeeded',
    model: null,
    detections: evidence.detections.map((item) => ({
      objectId: item.objectId,
      color: item.color,
      technique: item.technique
        ? {
            id: item.technique.id,
            name: item.technique.name,
            nameRu: item.technique.nameRu,
            color: item.technique.color ?? item.color ?? null
          }
        : {
            id: -(Math.abs(item.classId) + 1),
            name: item.className,
            nameRu: item.className,
            color: item.color ?? null
          },
      confidence: { detection: item.confidence.detection },
      bbox: {
        format: 'xywh_center',
        xCenter: null,
        yCenter: null,
        w: null,
        h: null,
        xCenterNorm: item.bbox.xCenterNorm,
        yCenterNorm: item.bbox.yCenterNorm,
        wNorm: item.bbox.wNorm,
        hNorm: item.bbox.hNorm
      }
    }))
  }
}

function techniqueComparison(item: ProgressTechniquePlanFact): {
  expected: string
  actual: string
} {
  return {
    expected: `${item.plan} ед. по плану`,
    actual: `${item.fact} ед. в наблюдениях`
  }
}

function messageToDeviation(
  message: ProgressDetailMessage,
  detail: DailyProgressDetail,
  index: number
): ProgressDeviation | null {
  if (message.category !== 'schedule' && message.category !== 'technique') {
    return null
  }
  const technique =
    message.techniqueId === null
      ? null
      : detail.techniques.items.find((item) => item.id === message.techniqueId)
  const comparison = technique
    ? techniqueComparison(technique)
    : {
        expected: detail.stages.next?.name ?? 'Этап по календарному плану',
        actual: detail.stages.current?.name ?? 'Не определено'
      }
  const category = message.category === 'schedule' ? 'timing' : 'equipment'
  return {
    id: `${detail.date}-${message.code}-${message.techniqueId ?? message.stageId ?? index}`,
    code: message.code,
    message: message.text,
    explanation: message.text,
    expected: comparison.expected,
    actual: comparison.actual,
    evidenceIds: message.evidencePhotoIds,
    category,
    categoryLabel: category === 'timing' ? 'Сроки' : 'Техника',
    icon: deviationIcons[message.code] ?? 'mdi-alert-circle-outline'
  }
}

export function adaptProgressDay(
  summary: DailyProgressSummary,
  detail: DailyProgressDetail | null,
  projectId: number
): DashboardDay {
  const selectedDetail = detail?.date === summary.date ? detail : null
  const quality = selectedDetail?.quality
  const equipment =
    selectedDetail?.techniques.items.map((item) => ({
      techniqueId: item.id,
      name: item.name,
      icon: 'mdi-excavator',
      plannedQuantity: item.plan,
      actualQuantity: item.fact,
      delta: item.delta,
      deviationType: item.status
    })) ?? []
  const deviations =
    selectedDetail?.messages
      .map((message, index) =>
        messageToDeviation(message, selectedDetail, index)
      )
      .filter((item): item is ProgressDeviation => item !== null) ?? []
  const timingTone =
    summary.status === 'behind'
      ? 'warning'
      : summary.status === 'ahead'
        ? 'info'
        : summary.status === 'unknown'
          ? 'neutral'
          : 'success'

  return {
    projectId,
    date: summary.date,
    actualStage: summary.stages.current?.name ?? null,
    currentStageScore: summary.stages.current?.score ?? null,
    stages: summary.stages,
    timingStatus: summary.status,
    timeDeviationDays: summary.deviationDays,
    observationCount: quality?.observations.total ?? 0,
    usableObservationCount: quality?.observations.usable ?? 0,
    processingCoverage: quality?.coverage ?? 0,
    agreementRate: quality?.agreement ?? null,
    dataQuality: quality?.level ?? summary.quality,
    dataQualityReasons:
      quality?.reasons.map((reason) => reasonLabels[reason] ?? reason) ?? [],
    equipment,
    evidencePhotos:
      selectedDetail?.evidence.map((item) =>
        evidenceToSnapshot(item, projectId)
      ) ?? [],
    timingLabel: timingLabels[summary.status],
    timingIcon:
      summary.status === 'unknown'
        ? 'mdi-help-circle-outline'
        : summary.status === 'behind'
          ? 'mdi-clock-alert-outline'
          : summary.status === 'ahead'
            ? 'mdi-arrow-top-right'
            : 'mdi-check-circle-outline',
    timingTone,
    qualityLabel: qualityLabels[quality?.level ?? summary.quality],
    coveragePercent: toPercent(quality?.coverage ?? 0),
    agreementPercent:
      quality === undefined ? null : toPercent(quality.agreement),
    deviations,
    deviationCount:
      summary.techniqueDeviationCount +
      (summary.status === 'ahead' || summary.status === 'behind' ? 1 : 0),
    message: summary.message
  }
}

export function emptyDashboardDay(projectId: number): DashboardDay {
  return adaptProgressDay(
    {
      date: '' as DateString,
      isFinal: false,
      status: 'unknown',
      deviationDays: null,
      techniqueDeviationCount: 0,
      message: {
        code: 'insufficient_data',
        severity: 'warning',
        text: 'Нет данных для отображения'
      },
      stages: { previous: null, current: null, next: null },
      quality: 'insufficient'
    },
    null,
    projectId
  )
}

export function filterProgressDeviations(
  deviations: ProgressDeviation[],
  category: ProgressCategory
): ProgressDeviation[] {
  return category === 'all'
    ? deviations
    : deviations.filter((deviation) => deviation.category === category)
}

export function formatProgressDate(
  date: string,
  options: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'long' }
): string {
  if (!date) return 'Нет данных'
  return new Intl.DateTimeFormat('ru-RU', {
    ...options,
    timeZone: 'UTC'
  }).format(new Date(`${date}T12:00:00Z`))
}
