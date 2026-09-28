export interface PaginatedListMetadata {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

export interface PaginatedList<T> {
  items: T[]
  metadata: PaginatedListMetadata
}

export interface PaginationParams {
  page?: number
  pageSize?: number
}

export type DateString = `${number}-${number}-${number}`

export type DateTimeString =
  `${number}-${number}-${number}T${number}:${number}:${number}.${number}Z`
