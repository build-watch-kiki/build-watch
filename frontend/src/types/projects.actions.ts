import type { DateString } from '@/types/api.ts'
import type { Project } from '@/types/projects.ts'

export interface CreateProjectPayload {
  startDate: DateString
  endDate: DateString
  name: string
  type: string
}

export type CreateProjectResponse = number

export interface UpdateProjectPayload {
  startDate: DateString
  endDate: DateString
  name: string
  type: string
}

export type UpdateProjectResponse = Project

export interface ProjectPathParams {
  projectId: number
}
