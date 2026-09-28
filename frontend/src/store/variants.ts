import { defineStore } from 'pinia'
import { api } from '@/store/api'
import type {
  PaginatedList,
  PaginatedListMetadata,
  PaginationParams
} from '@/types/api'
import type { ProjectType } from '@/types/projects'
import type { WorkType } from '@/types/plan'

export interface Technique {
  name: string
  nameRu: string
  id: number
  createdAt: string
}

interface CatalogState<T> {
  list: T[]
  pagination: PaginatedListMetadata | null
  loading: boolean
}

interface CatalogParams extends PaginationParams {
  search_value?: string
}

interface State {
  projectTypes: CatalogState<ProjectType>
  workTypes: CatalogState<WorkType>
  techniques: CatalogState<Technique>
}

export const useVariantsStore = defineStore('VariantsStore', {
  state: (): State => ({
    projectTypes: { list: [], pagination: null, loading: false },
    workTypes: { list: [], pagination: null, loading: false },
    techniques: { list: [], pagination: null, loading: false }
  }),

  getters: {
    getProjectTypes: (state: State): ProjectType[] => state.projectTypes.list,
    getProjectTypesPagination: (state: State): PaginatedListMetadata | null =>
      state.projectTypes.pagination,
    isProjectTypesLoading: (state: State): boolean =>
      state.projectTypes.loading,

    getWorkTypes: (state: State): WorkType[] => state.workTypes.list,
    getWorkTypesPagination: (state: State): PaginatedListMetadata | null =>
      state.workTypes.pagination,
    isWorkTypesLoading: (state: State): boolean => state.workTypes.loading,

    getTechniques: (state: State): Technique[] => state.techniques.list,
    getTechniquesPagination: (state: State): PaginatedListMetadata | null =>
      state.techniques.pagination,
    isTechniquesLoading: (state: State): boolean => state.techniques.loading,

    getPagination: (state: State): PaginatedListMetadata | null =>
      state.projectTypes.pagination,
    isListLoading: (state: State): boolean => state.projectTypes.loading
  },

  actions: {
    async loadProjectTypes(
      params: CatalogParams = {},
      opts: { append?: boolean } = {}
    ) {
      const { append = false } = opts
      this.projectTypes.loading = true
      try {
        const { data } = await api.get<PaginatedList<ProjectType>>(
          '/project-types',
          {
            params: {
              page: params.page ?? 1,
              pageSize: params.pageSize ?? 20,
              ...(params.search_value
                ? { search_value: params.search_value }
                : {})
            }
          }
        )
        if (append) {
          const existing = new Set(this.projectTypes.list.map((i) => i.id))
          const filtered = data.items.filter((i) => !existing.has(i.id))
          this.projectTypes.list = [...this.projectTypes.list, ...filtered]
        } else {
          this.projectTypes.list = data.items
        }
        this.projectTypes.pagination = data.metadata
      } finally {
        this.projectTypes.loading = false
      }
    },

    async loadWorkTypes(
      projectId: number | string,
      params: CatalogParams = {},
      opts: { append?: boolean } = {}
    ) {
      const { append = false } = opts
      this.workTypes.loading = true
      try {
        const { data } = await api.get<PaginatedList<WorkType>>(
          `/projects/${projectId}/work-types`,
          {
            params: {
              page: params.page ?? 1,
              pageSize: params.pageSize ?? 20,
              ...(params.search_value
                ? { search_value: params.search_value }
                : {})
            }
          }
        )
        if (append) {
          const existing = new Set(this.workTypes.list.map((i) => i.id))
          const filtered = data.items.filter((i) => !existing.has(i.id))
          this.workTypes.list = [...this.workTypes.list, ...filtered]
        } else {
          this.workTypes.list = data.items
        }
        this.workTypes.pagination = data.metadata
      } finally {
        this.workTypes.loading = false
      }
    },

    async loadTechniques(
      params: CatalogParams = {},
      opts: { append?: boolean } = {}
    ) {
      const { append = false } = opts
      this.techniques.loading = true
      try {
        const { data } = await api.get<PaginatedList<Technique>>(
          '/techniques',
          {
            params: {
              page: params.page ?? 1,
              pageSize: params.pageSize ?? 20,
              ...(params.search_value
                ? { search_value: params.search_value }
                : {})
            }
          }
        )
        if (append) {
          const existing = new Set(this.techniques.list.map((i) => i.id))
          const filtered = data.items.filter((i) => !existing.has(i.id))
          this.techniques.list = [...this.techniques.list, ...filtered]
        } else {
          this.techniques.list = data.items
        }
        this.techniques.pagination = data.metadata
      } finally {
        this.techniques.loading = false
      }
    }
  }
})
