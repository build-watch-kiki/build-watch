<script setup lang="ts" generic="T">
  import { computed, onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'

  import type { Catalog, PaginatedCatalog } from '@/types/catalogs'
  import NotFoundPlaceholder from '@/components/NotFoundPlaceholder.vue'
  import LoadingPlaceholder from '@/components/LoadingPlaceholder.vue'

  interface Props {
    modelValue: string | number | null | undefined
    catalog: Catalog<T> | PaginatedCatalog<T>
    selectedItem?: T | null

    allowSearch?: boolean

    itemValue?: string
    itemTitle?: string

    autofocus?: boolean

    label?: string
    placeholder?: string

    clearable?: boolean
    disabled?: boolean
    readonly?: boolean

    rules?: Array<(v: string | number | null) => true | string>

    density?: 'default' | 'comfortable' | 'compact'
    variant?:
      | 'outlined'
      | 'plain'
      | 'filled'
      | 'underlined'
      | 'solo'
      | 'solo-filled'
      | 'solo-inverted'
  }

  const props = withDefaults(defineProps<Props>(), {
    allowSearch: false,
    selectedItem: null,

    itemValue: 'id',
    itemTitle: 'name',

    autofocus: false,

    clearable: true,
    disabled: false,
    readonly: false,
    multiple: false,

    rules: undefined,

    density: 'comfortable',
    variant: 'outlined'
  })

  const emit = defineEmits<{
    'update:modelValue': [value: string | number | null | undefined]
  }>()

  const items = shallowRef<T[]>([])
  const loading = ref(false)
  const loadingMore = ref(false)
  const search = ref('')
  let lastFetchedSearch = ''

  function ensureSelectedItem() {
    const item = props.selectedItem as
      Record<string, unknown> | null | undefined
    if (!item) return
    const key = item[props.itemValue]
    if (key == null || String(key).trim() === '') return
    if (
      !items.value.some(
        (i) => (i as Record<string, unknown>)[props.itemValue] === key
      )
    ) {
      items.value = [props.selectedItem as T, ...items.value]
    }
  }

  const getKey = (item: T) =>
    String((item as Record<string, unknown>)[props.itemValue] ?? '').trim()

  const rootRef = ref<HTMLElement | null>(null)
  const menuWidth = shallowRef<number | undefined>(undefined)

  function updateMenuWidth() {
    const el = rootRef.value
    if (el) {
      menuWidth.value = el.getBoundingClientRect().width
    }
  }

  let resizeObserver: ResizeObserver | undefined

  let searchTimeout: ReturnType<typeof setTimeout> | undefined

  const isPaginated = computed(() => 'next' in props.catalog)

  const catalogLoading = computed(() => props.catalog.loading)

  const hasMore = computed(() => {
    if (!isPaginated.value) {
      return false
    }

    return (props.catalog as PaginatedCatalog<T>).hasMore
  })

  const component = computed(() =>
    props.allowSearch ? 'v-autocomplete' : 'v-select'
  )

  async function loadInitial() {
    if (props.selectedItem) {
      const sel = props.selectedItem as Record<string, unknown>
      const key = sel[props.itemValue]
      if (key != null && String(key).trim() !== '') {
        const exists = items.value.some(
          (i) =>
            String((i as Record<string, unknown>)[props.itemValue]) ===
            String(key)
        )
        if (!exists) {
          items.value = [props.selectedItem as T, ...items.value]
        }
      }
    }
    loading.value = true

    try {
      const result = await props.catalog.get()
      const hasSelected = (() => {
        const sel = props.selectedItem as Record<string, unknown> | null
        if (!sel) return false
        const key = sel[props.itemValue]
        if (key == null) return false
        return result.some(
          (i) =>
            String((i as Record<string, unknown>)[props.itemValue]) ===
            String(key)
        )
      })()
      if (hasSelected) {
        items.value = [...result]
      } else if (props.selectedItem) {
        const sel = props.selectedItem as Record<string, unknown>
        const key = sel[props.itemValue]
        if (key != null && String(key).trim() !== '') {
          items.value = [props.selectedItem as T, ...result]
        } else {
          items.value = [...result]
        }
      } else {
        items.value = [...result]
      }
      lastFetchedSearch = ''
    } finally {
      loading.value = false
    }
  }

  async function loadMore(options?: {
    done: (status: 'ok' | 'empty' | 'error') => void
  }) {
    const done = options?.done
    if (!isPaginated.value) {
      done?.('empty')
      return
    }

    if (loading.value || loadingMore.value || !hasMore.value) {
      done?.('empty')
      return
    }

    loadingMore.value = true

    try {
      const catalog = props.catalog as PaginatedCatalog<T>
      const result = await catalog.next()

      const resultKeys = new Set(
        result.map((item) => getKey(item)).filter(Boolean)
      )
      let base: T[] = items.value
      if (resultKeys.size) {
        base = base.filter((item) => {
          const k = getKey(item)
          return !k || !resultKeys.has(k)
        })
      }
      items.value = [...base, ...result]
      done?.(catalog.hasMore ? 'ok' : 'empty')
    } catch {
      done?.('error')
    } finally {
      loadingMore.value = false
    }
  }

  function handleInfiniteLoad(options: {
    done: (status: 'ok' | 'empty' | 'error') => void
  }) {
    void loadMore(options)
  }

  async function reloadBySearch() {
    const trimmed = search.value.trim()
    if (trimmed === lastFetchedSearch) return
    lastFetchedSearch = trimmed
    loading.value = true
    loadingMore.value = false

    try {
      if (isPaginated.value) {
        const catalog = props.catalog as PaginatedCatalog<T>
        catalog.reset()
      }

      const result = await props.catalog.get(trimmed || undefined)
      const hasSelected = (() => {
        const sel = props.selectedItem as Record<string, unknown> | null
        if (!sel) return false
        const key = sel[props.itemValue]
        if (key == null) return false
        return result.some(
          (i) =>
            String((i as Record<string, unknown>)[props.itemValue]) ===
            String(key)
        )
      })()
      if (hasSelected) {
        items.value = [...result]
      } else if (props.selectedItem) {
        const sel = props.selectedItem as Record<string, unknown>
        const key = sel[props.itemValue]
        const shouldMerge =
          !trimmed ||
          (() => {
            const title = sel[props.itemTitle]
            return (
              String(title ?? '').trim() === trimmed ||
              String(key ?? '').trim() === trimmed
            )
          })()
        if (shouldMerge && key != null && String(key).trim() !== '') {
          items.value = [props.selectedItem as T, ...result]
        } else {
          items.value = [...result]
        }
      } else {
        items.value = [...result]
      }
    } finally {
      loading.value = false
    }
  }

  function handleClear() {
    search.value = ''
    lastFetchedSearch = ''

    if (searchTimeout) {
      clearTimeout(searchTimeout)
      searchTimeout = undefined
    }

    if (isPaginated.value) {
      const catalog = props.catalog as PaginatedCatalog<T>
      catalog.reset()
    }

    void loadInitial()
  }

  function handleModelUpdate(value: unknown) {
    if (
      value === null ||
      value === undefined ||
      typeof value === 'string' ||
      typeof value === 'number'
    ) {
      emit('update:modelValue', value)
    }
  }

  watch(search, () => {
    if (!props.allowSearch) {
      return
    }

    const trimmed = search.value.trim()

    if (trimmed && String(props.modelValue ?? '').trim() === trimmed) {
      lastFetchedSearch = trimmed
      return
    }

    const sel = props.selectedItem as Record<string, unknown> | null
    if (sel) {
      const selVal = String(sel[props.itemValue] ?? '').trim()
      const selTitle = String(sel[props.itemTitle] ?? '').trim()
      if (trimmed && (trimmed === selVal || trimmed === selTitle)) {
        lastFetchedSearch = trimmed
        return
      }
    }

    const selectedTitles = new Set(
      String(props.modelValue ?? '')
        .split(',')
        .flatMap((v) => {
          const strVal = String(v).trim()
          if (!strVal) return []
          const found = items.value.find(
            (item) =>
              String((item as Record<string, unknown>)[props.itemValue]) ===
              strVal
          ) as Record<string, unknown> | undefined
          if (!found) return []
          const title = found[props.itemTitle]
          return title != null ? [String(title).trim()] : []
        })
    )

    if (trimmed && selectedTitles.has(trimmed)) {
      lastFetchedSearch = trimmed
      return
    }

    const exactMatch = items.value.some((item) => {
      const rec = item as Record<string, unknown>
      const title = rec[props.itemTitle]
      const val = rec[props.itemValue]
      return String(title).trim() === trimmed || String(val).trim() === trimmed
    })
    if (exactMatch && trimmed) {
      lastFetchedSearch = trimmed
      return
    }

    if (searchTimeout) {
      clearTimeout(searchTimeout)
    }

    searchTimeout = setTimeout(() => {
      void reloadBySearch()
    }, 300)
  })

  watch(
    () => props.selectedItem,
    () => {
      ensureSelectedItem()
    }
  )

  watch(
    () => props.catalog,
    () => {
      items.value = []
      search.value = ''
      lastFetchedSearch = ''

      if (searchTimeout) {
        clearTimeout(searchTimeout)
        searchTimeout = undefined
      }

      void loadInitial()
    }
  )

  onMounted(() => {
    void loadInitial()
    updateMenuWidth()
    if (rootRef.value) {
      resizeObserver = new ResizeObserver(() => updateMenuWidth())
      resizeObserver.observe(rootRef.value)
    }
    window.addEventListener('resize', updateMenuWidth)
  })

  onUnmounted(() => {
    if (searchTimeout) {
      clearTimeout(searchTimeout)
    }
    if (resizeObserver) {
      resizeObserver.disconnect()
      resizeObserver = undefined
    }
    window.removeEventListener('resize', updateMenuWidth)
  })
</script>

<template>
  <div ref="rootRef" class="catalog-selector">
    <component
      :is="component"
      v-model:search="search"
      :model-value="modelValue"
      :items="items"
      :loading="loading || catalogLoading ? 'primary' : false"
      :disabled="disabled"
      :readonly="readonly"
      :clearable="clearable"
      :multiple="false"
      :label="label"
      :placeholder="placeholder"
      :rules="rules"
      :item-value="itemValue"
      :item-title="itemTitle"
      :density="density"
      :variant="variant"
      :filter="() => true"
      :autofocus="autofocus"
      :menu-props="{
        maxHeight: 320,
        width: menuWidth,
        maxWidth: menuWidth,
        contentClass: 'catalog-selector-menu'
      }"
      @update:model-value="handleModelUpdate"
      @click:clear="handleClear"
    >
      <template #no-data>
        <NotFoundPlaceholder
          v-if="!(loading || loadingMore || catalogLoading)"
          text="Ничего не найдено"
          size="small"
          class="mt-3"
        />
      </template>
      <template v-if="isPaginated" #append-item>
        <v-infinite-scroll
          :disabled="!hasMore || loading || loadingMore"
          @load="handleInfiniteLoad"
        >
          <template #loading>
            <loading-placeholder size="small" text="Загрузка данных..." />
          </template>

          <template #empty>
            <span />
          </template>

          <template #error>
            <span />
          </template>
        </v-infinite-scroll>
      </template>
    </component>
  </div>
</template>

<style scoped>
  .catalog-selector {
    width: 100%;
  }
</style>

<style>
  .catalog-selector-menu .v-list-item-title {
    white-space: normal !important;
    word-break: break-word;
    overflow-wrap: anywhere;
  }

  .catalog-selector-menu .v-list-item {
    min-height: 48px;
    align-items: flex-start;
    padding-top: 8px;
    padding-bottom: 8px;
  }
</style>
