import type { DateString, DateTimeString } from '@/types/api.ts'

export interface ProjectType {
  name: string
  id: number
  createdAt: DateTimeString
}

export interface Project {
  startDate: DateString
  endDate: DateString
  id: number
  name: string
  createdAt: DateTimeString
  projectType: ProjectType
}
