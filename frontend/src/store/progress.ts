import { defineStore } from 'pinia'
import { api } from '@/store/api.ts'
import {
  createMockProgressDetail,
  createMockProgressHistory,
  isMockProject
} from '@/mock/index.ts'
import type {
  DailyProgressDetail,
  DailyProgressSummary,
  ProgressListResponse
} from '@/types/progress.ts'

interface ProgressState {
  history: DailyProgressSummary[]
  detail: DailyProgressDetail | null
  loading: { history: boolean; detail: boolean }
  error: { history: unknown; detail: unknown }
}

const historyRequests = new WeakMap<object, number>()
const detailRequests = new WeakMap<object, number>()

function nextRequest(counter: WeakMap<object, number>, store: object): number {
  const requestId = (counter.get(store) ?? 0) + 1
  counter.set(store, requestId)
  return requestId
}

export const useProjectProgressStore = defineStore('ProjectProgressStore', {
  state: (): ProgressState => ({
    history: [],
    detail: null,
    loading: { history: false, detail: false },
    error: { history: null, detail: null }
  }),

  getters: {
    getHistory: (state): DailyProgressSummary[] => state.history,
    getDetail: (state): DailyProgressDetail | null => state.detail
  },

  actions: {
    async loadHistory(projectId: number): Promise<void> {
      const requestId = nextRequest(historyRequests, this)
      this.loading.history = true
      this.error.history = null
      if (isMockProject(projectId)) {
        if (historyRequests.get(this) === requestId) {
          this.history = createMockProgressHistory()
          this.loading.history = false
        }
        return
      }
      try {
        const { data } = await api.get<
          ProgressListResponse<DailyProgressSummary>
        >(`/projects/${projectId}/progress/daily`)
        if (historyRequests.get(this) === requestId) this.history = data.items
      } catch (error) {
        if (historyRequests.get(this) === requestId) this.error.history = error
        throw error
      } finally {
        if (historyRequests.get(this) === requestId) {
          this.loading.history = false
        }
      }
    },

    async loadDetail(projectId: number, date: string): Promise<void> {
      const requestId = nextRequest(detailRequests, this)
      this.loading.detail = true
      this.error.detail = null
      if (isMockProject(projectId)) {
        if (detailRequests.get(this) === requestId) {
          this.detail = createMockProgressDetail(date)
          this.loading.detail = false
        }
        return
      }
      try {
        const { data } = await api.get<DailyProgressDetail>(
          `/projects/${projectId}/progress/daily/${date}`
        )
        if (detailRequests.get(this) === requestId) this.detail = data
      } catch (error) {
        if (detailRequests.get(this) === requestId) {
          this.detail = null
          this.error.detail = error
        }
        throw error
      } finally {
        if (detailRequests.get(this) === requestId) {
          this.loading.detail = false
        }
      }
    },

    reset(): void {
      nextRequest(historyRequests, this)
      nextRequest(detailRequests, this)
      this.history = []
      this.detail = null
      this.loading = { history: false, detail: false }
      this.error = { history: null, detail: null }
    }
  }
})
