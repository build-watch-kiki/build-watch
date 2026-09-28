import { defineStore } from 'pinia'
import { api } from '@/store/api.ts'
import type {
  Catalog,
  CatalogConfig,
  CatalogStoreCache,
  PaginatedCatalog
} from '@/types/catalogs.ts'
import type { PaginatedList, PaginatedListMetadata } from '@/types/api.ts'

interface State {
  catalogs: Record<string, CatalogConfig>
  cache: Record<string, CatalogStoreCache<unknown>>
}

export const useCatalogsStore = defineStore('CatalogsStore', {
  state: (): State => ({
    catalogs: {
      projectTypes: {
        url: '/project-types',
        paginated: true,
        allowSearch: true
      }
    },
    cache: {}
  }),

  actions: {
    add(catalogName: string, config: CatalogConfig): void {
      if (this.catalogs[catalogName]) {
        throw new Error(`Catalog "${catalogName}" is already registered`)
      }
      this.catalogs[catalogName] = config
    },

    create<T>(catalogName: string): PaginatedCatalog<T> | Catalog<T> {
      const config = this.catalogs[catalogName]
      if (!config) {
        throw new Error(`Catalog "${catalogName}" is not registered`)
      }

      if (!config.paginated) {
        return this.createCatalog<T>(config)
      }
      return this.createPaginatedCatalog<T>(config)
    },

    async initLoad<T>(
      catalogName: string,
      config: CatalogConfig
    ): Promise<void> {
      if (!this.catalogs[catalogName]) {
        this.add(catalogName, config)
      }
      if (this.cache[catalogName]) {
        return
      }
      const response = await api.get<PaginatedList<T>>(config.url, {
        params: {
          page: 1,
          pageSize: 100
        }
      })
      this.cache[catalogName] = {
        items: response.data.items,
        metadata: response.data.metadata,
        searchValue: null
      }
    },

    createCatalog<T>(config: CatalogConfig): Catalog<T> {
      let loading = false
      return {
        get loading() {
          return loading
        },
        async get(search?: string): Promise<T[]> {
          loading = true
          try {
            const { data } = await api.get<T[]>(config.url, {
              params: config.allowSearch
                ? {
                    search_value: search
                  }
                : undefined
            })
            return data
          } finally {
            loading = false
          }
        }
      }
    },

    createPaginatedCatalog<T>(config: CatalogConfig): PaginatedCatalog<T> {
      let loading = false
      let page = 0
      let searchValue: string | undefined

      let metadata: PaginatedListMetadata | null = null

      const items: T[] = []

      const catalog: PaginatedCatalog<T> = {
        get loading() {
          return loading
        },
        get hasMore() {
          if (!metadata) {
            return true
          }
          return metadata.page < metadata.totalPages
        },
        async get(search?: string): Promise<T[]> {
          loading = true

          try {
            page = 1
            searchValue = search

            const { data } = await api.get<PaginatedList<T>>(config.url, {
              params: {
                page,
                pageSize: 20,
                ...(config.allowSearch && search
                  ? {
                      search_value: search
                    }
                  : {})
              }
            })
            items.splice(0, items.length, ...data.items)
            metadata = data.metadata
            return data.items
          } finally {
            loading = false
          }
        },
        async next(): Promise<T[]> {
          if (!catalog.hasMore || loading) {
            return []
          }
          loading = true
          try {
            const nextPage = page + 1

            const { data } = await api.get<PaginatedList<T>>(config.url, {
              params: {
                page: nextPage,
                pageSize: 20,
                ...(config.allowSearch && searchValue
                  ? {
                      search_value: searchValue
                    }
                  : {})
              }
            })
            page = nextPage
            items.push(...data.items)
            metadata = data.metadata
            return data.items
          } finally {
            loading = false
          }
        },
        reset(): void {
          page = 0
          searchValue = undefined
          metadata = null
          items.splice(0)
        }
      }
      return catalog
    }
  }
})
