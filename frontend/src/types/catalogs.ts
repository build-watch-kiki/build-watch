import type { PaginatedListMetadata } from '@/types/api.ts'

export interface CatalogConfig {
  url: string
  paginated: boolean
  allowSearch: boolean
}

export interface Catalog<T> {
  loading: boolean
  get(search?: string): Promise<T[]>
}

export interface PaginatedCatalog<T> extends Catalog<T> {
  next(): Promise<T[]>
  reset(): void
  hasMore: boolean
}

export interface CatalogStoreCache<T> {
  items: T[]
  metadata: PaginatedListMetadata | null
  searchValue: string | null
}
