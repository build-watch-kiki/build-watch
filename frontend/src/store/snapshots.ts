import { defineStore } from 'pinia'
import type {
  DefaultStoreLoadingActionState,
  DefaultStorePaginatedState
} from '@/types/store.ts'
import type { PaginatedList } from '@/types/api.ts'
import { api } from '@/store/api.ts'
import type { Snapshot } from '@/types/snapshots.ts'
import type { PhotoResponse } from '@/types/photos.ts'
import { adaptPhoto } from '@/utils/photos.ts'
import type {
  CreateSnapshotPayload,
  CreateSnapshotResponse,
  SnapshotsListParams,
  SnapshotsPathParams
} from '@/types/snapshots.actions.ts'
import {
  addMockPhotoFromFile,
  getMockPhoto,
  isMockProject,
  listMockPhotos
} from '@/mock/index.ts'

type State = DefaultStorePaginatedState<
  Snapshot,
  DefaultStoreLoadingActionState
>

// Track the active list request without changing public state.
const listRequests = new WeakMap<object, number>()
const detailRequests = new WeakMap<object, number>()

export const useProjectSnapshotsStore = defineStore('ProjectSnapshotsStore', {
  state: (): State => {
    return {
      list: [],
      detail: null,
      pagination: null,
      error: null,
      loading: {
        list: false,
        detail: false,
        action: false
      }
    }
  },
  getters: {
    getList: (state) => state.list,
    getDetail: (state) => state.detail,
    getPagination: (state) => state.pagination,
    getLoadingState: (state) => state.loading
  },
  actions: {
    async loadPaginatedList(
      { projectId }: SnapshotsPathParams,
      params: SnapshotsListParams = {},
      append = false,
      silent = false
    ) {
      const requestId = (listRequests.get(this) ?? 0) + 1
      listRequests.set(this, requestId)
      if (isMockProject(projectId)) {
        try {
          if (!silent) this.loading.list = true
          const { items, total } = listMockPhotos({
            page: params.page,
            pageSize: params.pageSize,
            isProcessed: params.isProcessed
          })
          if (listRequests.get(this) !== requestId) return
          const adapted = items.map((item) => adaptPhoto(item, projectId))
          if (append) {
            this.list = [...this.list, ...adapted]
          } else {
            this.list = adapted
          }
          const pageSize = params.pageSize ?? 20
          this.pagination = {
            page: params.page ?? 1,
            pageSize,
            total,
            totalPages: Math.max(1, Math.ceil(total / pageSize))
          }
        } finally {
          if (listRequests.get(this) === requestId && !silent) {
            this.loading.list = false
          }
        }
        return
      }
      try {
        if (!silent) this.loading.list = true
        const { data } = await api.get<PaginatedList<PhotoResponse>>(
          `/projects/${projectId}/photos`,
          {
            params
          }
        )
        if (listRequests.get(this) !== requestId) return
        const items = data.items.map((item) => adaptPhoto(item, projectId))
        if (append) {
          this.list = [...this.list, ...items]
        } else {
          this.list = items
        }
        this.pagination = data.metadata
      } finally {
        if (listRequests.get(this) === requestId && !silent) {
          this.loading.list = false
        }
      }
    },
    async loadDetail({
      projectId,
      photoId
    }: SnapshotsPathParams & { photoId: number }) {
      const requestId = (detailRequests.get(this) ?? 0) + 1
      detailRequests.set(this, requestId)
      if (isMockProject(projectId)) {
        try {
          this.loading.detail = true
          this.detail = null
          const found = getMockPhoto(photoId)
          if (detailRequests.get(this) === requestId) {
            this.detail = found ? adaptPhoto(found, projectId) : null
          }
        } finally {
          if (detailRequests.get(this) === requestId)
            this.loading.detail = false
        }
        return
      }
      try {
        this.loading.detail = true
        this.detail = null
        const { data } = await api.get<PhotoResponse>(
          `/projects/${projectId}/photos/${photoId}`
        )
        if (detailRequests.get(this) === requestId) {
          this.detail = adaptPhoto(data, projectId)
        }
      } finally {
        if (detailRequests.get(this) === requestId) this.loading.detail = false
      }
    },
    clearDetail() {
      const requestId = (detailRequests.get(this) ?? 0) + 1
      detailRequests.set(this, requestId)
      this.detail = null
      this.loading.detail = false
    },
    async createItem(
      { projectId }: SnapshotsPathParams,
      payload: CreateSnapshotPayload
    ): Promise<CreateSnapshotResponse> {
      if (isMockProject(projectId)) {
        const file = payload.get('file')
        if (!(file instanceof File)) {
          throw new Error('Mock upload expects a "file" field')
        }
        const capturedAt = payload.get('capturedAt')
        return {
          id: addMockPhotoFromFile(
            file,
            typeof capturedAt === 'string' && capturedAt ? capturedAt : null
          ).id
        }
      }
      try {
        this.loading.action = true
        const { data } = await api.post<CreateSnapshotResponse>(
          `/projects/${projectId}/photos`,
          payload
        )
        return data
      } finally {
        this.loading.action = false
      }
    }
  }
})
