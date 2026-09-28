import type { PaginatedListMetadata } from '@/types/api.ts'

export interface DefaultStoreState<T, L> {
  list: T[]
  detail: T | null
  loading: L
  error: string | null
}

export interface DefaultStorePaginatedState<T, L> extends DefaultStoreState<
  T,
  L
> {
  pagination: PaginatedListMetadata | null
}

export interface DefaultStoreLoadingState {
  list: boolean
  detail: boolean
}

export interface DefaultStoreLoadingActionState extends DefaultStoreLoadingState {
  action: boolean
}
