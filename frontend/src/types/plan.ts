import type { DateString, DateTimeString } from '@/types/api.ts'
import type { StageActualProgress } from '@/types/progress.ts'

export interface Requirement {
  name: string
  nameRu: string
  id: number
  createdAt: DateTimeString
  quantity: number
}

export interface Stage {
  startDate: DateString
  endDate: DateString
  id: number
  parentId: number
  createdAt: DateTimeString
  workTypeId: number
  workTypeName: string
  requiresTechnique: Requirement[]
  actual?: StageActualProgress | null
}

export interface WorkType {
  name: string
  id: number
  createdAt: DateTimeString
}
