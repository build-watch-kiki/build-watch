<script setup lang="ts">
  import { computed, onMounted, ref, watch } from 'vue'
  import { storeToRefs } from 'pinia'
  import { useVariantsStore } from '@/store/variants.ts'

  interface Props {
    modelValue?: number | null
    projectId: number | string
    label?: string
    placeholder?: string
    disabled?: boolean
    clearable?: boolean
    rules?: unknown[]
  }

  const props = withDefaults(defineProps<Props>(), {
    modelValue: null,
    label: 'Вид работы',
    placeholder: 'Выберите вид работы',
    disabled: false,
    clearable: true,
    rules: undefined
  })

  const emit = defineEmits<{
    'update:modelValue': [value: number | null]
  }>()

  const variantsStore = useVariantsStore()
  const { workTypes } = storeToRefs(variantsStore)

  const search = ref('')
  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  let lastFetchedSearch = ''

  const selectItems = computed(() =>
    workTypes.value.list.map((item) => ({
      title: item.name,
      value: item.id
    }))
  )

  const internalValue = computed({
    get: () => props.modelValue ?? null,
    set: (value: number | null) => emit('update:modelValue', value)
  })

  function onUpdateSearch(value: string) {
    const trimmed = value.trim()
    if (trimmed === lastFetchedSearch) {
      search.value = value
      return
    }
    const selected = workTypes.value.list.find(
      (t) => t.id === internalValue.value
    )
    if (selected && selected.name === value) {
      search.value = value
      lastFetchedSearch = trimmed
      return
    }
    search.value = value
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(async () => {
      const q = search.value.trim()
      if (q === lastFetchedSearch) return
      lastFetchedSearch = q
      await variantsStore.loadWorkTypes(props.projectId, {
        search_value: q || undefined,
        page: 1,
        pageSize: 20
      })
    }, 300)
  }

  async function onLoadMore() {
    const pagination = workTypes.value.pagination
    if (!pagination) return
    if (pagination.page >= pagination.totalPages) return
    if (workTypes.value.loading) return
    await variantsStore.loadWorkTypes(
      props.projectId,
      {
        search_value: search.value.trim() || undefined,
        page: pagination.page + 1,
        pageSize: pagination.pageSize
      },
      { append: true }
    )
  }

  let scrollHandler: ((e: Event) => void) | null = null
  let scrollEl: HTMLElement | null = null

  function attachScrollListener() {
    requestAnimationFrame(() => {
      const el = document.querySelector(
        '.v-overlay--active .v-list'
      ) as HTMLElement | null
      if (!el || el === scrollEl) return
      if (scrollEl && scrollHandler) {
        scrollEl.removeEventListener('scroll', scrollHandler)
      }
      scrollEl = el
      scrollHandler = () => {
        if (!el) return
        if (el.scrollTop + el.clientHeight >= el.scrollHeight - 40) {
          void onLoadMore()
        }
      }
      el.addEventListener('scroll', scrollHandler)
    })
  }

  function handleMenuUpdate(open: boolean) {
    if (!open) {
      if (scrollEl && scrollHandler) {
        scrollEl.removeEventListener('scroll', scrollHandler)
        scrollEl = null
        scrollHandler = null
      }
      return
    }
    attachScrollListener()
  }

  onMounted(async () => {
    if (!props.projectId) return
    await variantsStore.loadWorkTypes(props.projectId, {
      page: 1,
      pageSize: 20
    })
  })

  watch(
    () => props.projectId,
    async (id) => {
      if (!id) return
      search.value = ''
      await variantsStore.loadWorkTypes(id, {
        page: 1,
        pageSize: 20
      })
    }
  )
</script>

<template>
  <v-autocomplete
    v-model="internalValue"
    :items="selectItems"
    :label="props.label"
    :placeholder="props.placeholder"
    :loading="workTypes.loading"
    :disabled="props.disabled"
    :clearable="props.clearable"
    :rules="props.rules as any"
    variant="outlined"
    density="comfortable"
    no-data-text="Виды работ не найдены"
    auto-select-first
    :menu-props="{
      maxHeight: 320,
      maxWidth: 560,
      width: 560,
      contentClass: 'worktype-menu'
    }"
    @update:search="onUpdateSearch"
    @update:menu="handleMenuUpdate"
  />
</template>

<style>
  .worktype-menu .v-list-item-title {
    white-space: normal !important;
    word-break: break-word;
    overflow-wrap: anywhere;
  }

  .worktype-menu .v-list-item {
    min-height: 48px;
    align-items: flex-start;
    padding-top: 8px;
    padding-bottom: 8px;
  }
</style>
