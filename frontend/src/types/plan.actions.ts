import type { DateString } from '@/types/api.ts'
import type { Stage } from '@/types/plan.ts'
import type { ProjectPathParams } from '@/types/projects.actions.ts'

export interface TechniquePayload {
  name: string
  quantity: number
}

export interface CreateStagePayload {
  startDate: DateString
  endDate: DateString
  parentId: number | null
  workTypeId: number
  techniques: TechniquePayload[]
}

export type CreateStageResponse = number

export interface UpdateStagePayload {
  startDate: DateString
  endDate: DateString
  parentId: number | null
  workTypeId: number
}

export type UpdateStageResponse = Stage

export interface UpdateStageTechniquesPayload {
  techniques: TechniquePayload[]
}

export type UpdateStageTechniquesResponse = Stage

export type PlanPathParams = ProjectPathParams

export interface StagePathParams extends ProjectPathParams {
  stageId: number
}
