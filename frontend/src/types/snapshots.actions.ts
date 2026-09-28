import type { ProjectPathParams } from '@/types/projects.actions.ts'
import type { PaginationParams } from '@/types/api.ts'

export type CreateSnapshotPayload = FormData

export interface CreateSnapshotResponse {
  id: number
}

export type SnapshotsPathParams = ProjectPathParams

export interface SnapshotsListParams extends PaginationParams {
  isProcessed?: boolean
}
