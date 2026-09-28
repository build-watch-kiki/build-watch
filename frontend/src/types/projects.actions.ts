import type { DateString } from '@/types/api.ts'

export interface CreateProjectPayload {
  startDate: DateString
  endDate: DateString
  name: string
  type: string
}

export type CreateProjectResponse = number

export interface ProjectPathParams {
  projectId: number
}
