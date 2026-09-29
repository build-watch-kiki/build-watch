import type { DateTimeString } from '@/types/api.ts'
import type { PhotoResponse } from '@/types/photos.ts'
import type { Requirement, Stage } from '@/types/plan.ts'
import type {
  CreateStagePayload,
  UpdateStagePayload,
  UpdateStageTechniquesPayload
} from '@/types/plan.actions.ts'
import { MOCK_PHOTOS, MOCK_PHOTO_HEIGHT, MOCK_PHOTO_WIDTH } from './photos.ts'
import { MOCK_STAGES } from './stages.ts'

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

function nowIso(): DateTimeString {
  return new Date().toISOString() as DateTimeString
}

let photos: PhotoResponse[] = clone(MOCK_PHOTOS)
let stages: Stage[] = clone(MOCK_STAGES)

export function resetMockDb(): void {
  photos = clone(MOCK_PHOTOS)
  stages = clone(MOCK_STAGES)
}

export function listMockPhotos(params: {
  page?: number
  pageSize?: number
  isProcessed?: boolean
}): { items: PhotoResponse[]; total: number } {
  const filtered = (
    params.isProcessed === undefined || params.isProcessed === null
      ? photos
      : photos.filter((photo) => photo.isProcessed === params.isProcessed)
  )
    .slice()
    .sort((a, b) => (b.capturedAt ?? '').localeCompare(a.capturedAt ?? ''))
  const page = params.page ?? 1
  const pageSize = params.pageSize ?? 20
  const start = (page - 1) * pageSize
  return {
    items: clone(filtered.slice(start, start + pageSize)),
    total: filtered.length
  }
}

export function getMockPhoto(photoId: number): PhotoResponse | undefined {
  const found = photos.find((photo) => photo.id === photoId)
  return found ? clone(found) : undefined
}

export function addMockPhotoFromFile(
  file: File,
  capturedAt?: string | null
): PhotoResponse {
  const id = photos.reduce((max, photo) => Math.max(max, photo.id), 100) + 1
  const item: PhotoResponse = {
    id,
    name: file.name,
    url: URL.createObjectURL(file),
    capturedAt: capturedAt
      ? capturedAt.includes('T')
        ? capturedAt
        : `${capturedAt}T00:00:00.000Z`
      : nowIso(),
    createdAt: nowIso(),
    isProcessed: true,
    processingStatus: 'succeeded',
    width: MOCK_PHOTO_WIDTH,
    height: MOCK_PHOTO_HEIGHT,
    format: file.type,
    model: { name: 'mock-road', version: '1.0', weights: 'mock' },
    detections: []
  }
  photos = [item, ...photos]
  return clone(item)
}

export function listMockStages(): Stage[] {
  return clone(stages)
}

function nextStageId(): number {
  return stages.reduce((max, stage) => Math.max(max, stage.id), 0) + 1
}

function toRequirement(
  technique: { name: string; quantity: number },
  index: number
): Requirement {
  return {
    id: index,
    name: technique.name,
    nameRu: technique.name,
    createdAt: nowIso(),
    quantity: technique.quantity
  }
}

export function createMockStage(payload: CreateStagePayload): number {
  const id = nextStageId()
  stages = [
    ...stages,
    {
      id,
      parentId: payload.parentId ?? 0,
      workTypeId: payload.workTypeId,
      workTypeName: `Вид работ ${payload.workTypeId}`,
      startDate: payload.startDate,
      endDate: payload.endDate,
      createdAt: nowIso(),
      requiresTechnique: payload.techniques.map(toRequirement),
      actual: null
    }
  ]
  return id
}

export function updateMockStage(
  stageId: number,
  payload: UpdateStagePayload
): Stage | undefined {
  const index = stages.findIndex((stage) => stage.id === stageId)
  if (index === -1) return undefined
  const current = stages[index]!
  const updated: Stage = {
    ...current,
    startDate: payload.startDate,
    endDate: payload.endDate,
    parentId: payload.parentId ?? 0,
    workTypeId: payload.workTypeId,
    workTypeName:
      payload.workTypeId === current.workTypeId
        ? current.workTypeName
        : `Вид работ ${payload.workTypeId}`
  }
  stages = stages.map((stage) => (stage.id === stageId ? updated : stage))
  return clone(updated)
}

export function updateMockStageTechniques(
  stageId: number,
  payload: UpdateStageTechniquesPayload
): Stage | undefined {
  const index = stages.findIndex((stage) => stage.id === stageId)
  if (index === -1) return undefined
  const updated: Stage = {
    ...stages[index]!,
    requiresTechnique: payload.techniques.map(toRequirement)
  }
  stages = stages.map((stage) => (stage.id === stageId ? updated : stage))
  return clone(updated)
}

export function deleteMockStage(stageId: number): void {
  const doomed = new Set<number>([stageId])
  let expanded = true
  while (expanded) {
    expanded = false
    for (const stage of stages) {
      if (!doomed.has(stage.id) && doomed.has(stage.parentId)) {
        doomed.add(stage.id)
        expanded = true
      }
    }
  }
  stages = stages.filter((stage) => !doomed.has(stage.id))
}
