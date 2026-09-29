import { defineStore } from 'pinia'
import type { Project } from '@/types/projects'
import { api } from '@/store/api'
import { MOCK_PROJECT, isMockProject, isMockShown } from '@/mock/index.ts'
import type { PaginatedList, PaginationParams } from '@/types/api'
import type {
  DefaultStoreLoadingActionState,
  DefaultStorePaginatedState
} from '@/types/store.ts'
import type {
  CreateProjectPayload,
  CreateProjectResponse,
  ProjectPathParams,
  UpdateProjectPayload,
  UpdateProjectResponse
} from '@/types/projects.actions.ts'

type State = DefaultStorePaginatedState<Project, DefaultStoreLoadingActionState>

// Track the active detail request per store without changing its public state.
const detailRequests = new WeakMap<object, number>()

export const useProjectsStore = defineStore('ProjectsStore', {
  state: (): State => ({
    list: [],
    pagination: null,
    detail: null,
    loading: {
      list: false,
      detail: false,
      action: false
    },
    error: null
  }),
  getters: {
    getList: (state) => state.list,
    getDetail: (state) => state.detail,
    getPagination: (state) => state.pagination,
    getLoadingState: (state) => state.loading
  },
  actions: {
    async loadPaginatedList(params: PaginationParams = {}, append = false) {
      try {
        this.loading.list = true
        const { data } = await api.get<PaginatedList<Project>>('/projects', {
          params
        })
        if (append) {
          this.list = [...this.list, ...data.items]
        } else if (isMockShown() && (params.page ?? 1) === 1) {
          this.list = [MOCK_PROJECT, ...data.items]
        } else {
          this.list = data.items
        }
        this.pagination = isMockShown()
          ? {
              ...data.metadata,
              total: data.metadata.total + 1,
              totalPages: Math.ceil(
                (data.metadata.total + 1) / data.metadata.pageSize
              )
            }
          : data.metadata
      } finally {
        this.loading.list = false
      }
    },
    async createItem(
      payload: CreateProjectPayload
    ): Promise<CreateProjectResponse> {
      try {
        this.loading.action = true
        const { data } = await api.post<CreateProjectResponse>(
          '/projects',
          payload
        )
        return data
      } finally {
        this.loading.action = false
      }
    },
    async updateItem(
      { projectId }: ProjectPathParams,
      payload: UpdateProjectPayload
    ): Promise<UpdateProjectResponse> {
      if (isMockProject(projectId)) {
        const updated: Project = {
          ...(this.detail?.id === projectId
            ? this.detail
            : (this.list.find((project) => project.id === projectId) ??
              MOCK_PROJECT)),
          ...payload
        }
        this.list = this.list.map((project) =>
          project.id === projectId ? updated : project
        )
        if (this.detail?.id === projectId) this.detail = updated
        return updated
      }
      try {
        this.loading.action = true
        const { data } = await api.put<UpdateProjectResponse>(
          `/projects/${projectId}`,
          payload
        )
        return data
      } finally {
        this.loading.action = false
      }
    },
    async loadDetail({ projectId }: ProjectPathParams) {
      const requestId = (detailRequests.get(this) ?? 0) + 1
      detailRequests.set(this, requestId)
      if (isMockProject(projectId)) {
        try {
          this.loading.detail = true
          if (detailRequests.get(this) === requestId) this.detail = MOCK_PROJECT
        } finally {
          if (detailRequests.get(this) === requestId) {
            this.loading.detail = false
          }
        }
        return
      }
      try {
        this.loading.detail = true
        const { data } = await api.get<Project>(`/projects/${projectId}`)
        if (detailRequests.get(this) === requestId) this.detail = data
      } finally {
        if (detailRequests.get(this) === requestId) this.loading.detail = false
      }
    },
    async deleteItem({ projectId }: ProjectPathParams) {
      if (isMockProject(projectId)) {
        this.list = this.list.filter((project) => project.id !== projectId)
        if (this.detail?.id === projectId) this.detail = null
        return
      }
      try {
        this.loading.action = true
        await api.delete<Project>(`/projects/${projectId}`)
      } finally {
        this.loading.action = false
      }
    }
  }
})
