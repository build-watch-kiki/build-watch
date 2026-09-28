import { defineStore } from 'pinia'
import type { Stage } from '@/types/plan.ts'
import { api } from '@/store/api.ts'
import {
  createMockStage,
  deleteMockStage,
  isMockProject,
  listMockStages,
  updateMockStage,
  updateMockStageTechniques
} from '@/mock/index.ts'
import type {
  DefaultStoreLoadingActionState,
  DefaultStoreState
} from '@/types/store.ts'
import type {
  CreateStagePayload,
  CreateStageResponse,
  PlanPathParams,
  StagePathParams,
  UpdateStagePayload,
  UpdateStageResponse,
  UpdateStageTechniquesPayload,
  UpdateStageTechniquesResponse
} from '@/types/plan.actions.ts'

type State = DefaultStoreState<Stage, DefaultStoreLoadingActionState>

// Only publish the most recent plan response when switching objects.
const listRequests = new WeakMap<object, number>()

export const useProjectPlanStore = defineStore('ProjectPlanStore', {
  state: (): State => ({
    list: [],
    detail: null,
    loading: {
      list: false,
      detail: false,
      action: false
    },
    error: null
  }),

  getters: {
    getList: (state): Stage[] => state.list,
    getDetail: (state) => state.detail,
    getStageById:
      (state: State): ((id: number) => Stage | undefined) =>
      (id) =>
        state.list.find((s) => s.id === id),
    getLoadingState: (state) => state.loading
  },

  actions: {
    async loadList({ projectId }: PlanPathParams) {
      const requestId = (listRequests.get(this) ?? 0) + 1
      listRequests.set(this, requestId)
      if (isMockProject(projectId)) {
        try {
          this.loading.list = true
          if (listRequests.get(this) === requestId) {
            this.list = listMockStages()
          }
        } finally {
          if (listRequests.get(this) === requestId) this.loading.list = false
        }
        return
      }
      try {
        this.loading.list = true
        const { data } = await api.get<{ items: Stage[] }>(
          `/projects/${projectId}/stages/gantt`
        )
        if (listRequests.get(this) === requestId) this.list = data.items
      } finally {
        if (listRequests.get(this) === requestId) this.loading.list = false
      }
    },

    async createItem(
      { projectId }: PlanPathParams,
      payload: CreateStagePayload
    ): Promise<CreateStageResponse> {
      if (isMockProject(projectId)) {
        const id = createMockStage(payload)
        await this.loadList({ projectId })
        return id
      }
      try {
        this.loading.action = true
        const { data } = await api.post<CreateStageResponse>(
          `/projects/${projectId}/stages`,
          payload
        )
        await this.loadList({ projectId })
        return data
      } finally {
        this.loading.action = false
      }
    },

    async updateItem(
      { projectId, stageId }: StagePathParams,
      payload: UpdateStagePayload
    ): Promise<UpdateStageResponse> {
      if (isMockProject(projectId)) {
        const updated = updateMockStage(stageId, payload)
        if (!updated) throw new Error(`Mock stage "${stageId}" not found`)
        await this.loadList({ projectId })
        return updated
      }
      try {
        this.loading.action = true
        const { data } = await api.put<UpdateStageResponse>(
          `/projects/${projectId}/stages/${stageId}`,
          payload
        )
        await this.loadList({ projectId })
        return data
      } finally {
        this.loading.action = false
      }
    },

    async updateTechniques(
      { projectId, stageId }: StagePathParams,
      payload: UpdateStageTechniquesPayload
    ): Promise<UpdateStageTechniquesResponse> {
      if (isMockProject(projectId)) {
        const updated = updateMockStageTechniques(stageId, payload)
        if (!updated) throw new Error(`Mock stage "${stageId}" not found`)
        await this.loadList({ projectId })
        return updated
      }
      try {
        this.loading.action = true
        const { data } = await api.put<UpdateStageTechniquesResponse>(
          `/projects/${projectId}/stages/${stageId}/techniques`,
          payload
        )
        await this.loadList({ projectId })
        return data
      } finally {
        this.loading.action = false
      }
    },

    async deleteItem({ projectId, stageId }: StagePathParams): Promise<void> {
      if (isMockProject(projectId)) {
        deleteMockStage(stageId)
        await this.loadList({ projectId })
        return
      }
      try {
        this.loading.action = true
        await api.delete(`/projects/${projectId}/stages/${stageId}`)
        await this.loadList({ projectId })
      } finally {
        this.loading.action = false
      }
    }
  }
})
