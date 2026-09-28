<script setup lang="ts">
  import { computed, ref, watch } from 'vue'
  import type { DataTableHeader } from 'vuetify/framework'

  import { useVariantsStore } from '@/store/variants.ts'
  import { displayDate } from '@/utils/datetime'
  import LoadingPlaceholder from '@/components/LoadingPlaceholder.vue'
  import NoDataPlaceholder from '@/components/NoDataPlaceholder.vue'

  type CatalogKey = 'workTypes' | 'techniques' | 'projectTypes'

  interface Props {
    catalog: CatalogKey
    projectId: number
    description: string
  }

  const props = defineProps<Props>()

  const variantsStore = useVariantsStore()

  const page = ref(1)
  const itemsPerPage = ref(10)
  const search = ref('')
  const error = ref<string | null>(null)

  let searchTimer: ReturnType<typeof setTimeout> | null = null

  const list = computed(() => {
    switch (props.catalog) {
      case 'workTypes':
        return variantsStore.getWorkTypes
      case 'techniques':
        return variantsStore.getTechniques
      default:
        return variantsStore.getProjectTypes
    }
  })

  const pagination = computed(() => {
    switch (props.catalog) {
      case 'workTypes':
        return variantsStore.getWorkTypesPagination
      case 'techniques':
        return variantsStore.getTechniquesPagination
      default:
        return variantsStore.getProjectTypesPagination
    }
  })

  const loading = computed(() => {
    switch (props.catalog) {
      case 'workTypes':
        return variantsStore.isWorkTypesLoading
      case 'techniques':
        return variantsStore.isTechniquesLoading
      default:
        return variantsStore.isProjectTypesLoading
    }
  })

  const headers = computed<DataTableHeader[]>(() => {
    switch (props.catalog) {
      case 'workTypes':
        return [
          { title: 'Название', key: 'name', sortable: false },
          { title: 'Дата создания', key: 'createdAt', sortable: false }
        ]
      case 'techniques':
        return [
          { title: 'Название', key: 'nameRu', sortable: false },
          { title: 'Системное имя', key: 'name', sortable: false },
          { title: 'ID', key: 'id', sortable: false }
        ]
      default:
        return [
          { title: 'Название', key: 'name', sortable: false },
          { title: 'ID', key: 'id', sortable: false }
        ]
    }
  })

  async function load() {
    error.value = null
    const params = {
      page: page.value,
      pageSize: itemsPerPage.value,
      ...(search.value.trim() ? { search_value: search.value.trim() } : {})
    }
    try {
      switch (props.catalog) {
        case 'workTypes':
          await variantsStore.loadWorkTypes(props.projectId, params)
          break
        case 'techniques':
          await variantsStore.loadTechniques(params)
          break
        case 'projectTypes':
          await variantsStore.loadProjectTypes(params)
          break
      }
    } catch {
      error.value = 'Не удалось загрузить каталог'
    }
  }

  function handleUpdateOptions(options: {
    page: number
    itemsPerPage: number
  }) {
    page.value = options.page
    itemsPerPage.value = options.itemsPerPage
    void load()
  }

  watch(search, () => {
    if (searchTimer) clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      page.value = 1
      void load()
    }, 400)
  })

  watch(
    () => [props.catalog, props.projectId],
    () => {
      page.value = 1
      search.value = ''
      void load()
    }
  )

  function rawOf<T>(item: unknown): T {
    return ((item as { raw?: T }).raw ?? item) as T
  }
</script>

<template>
  <div class="catalog-tab">
    <p class="bw-muted catalog-tab__description">{{ props.description }}</p>

    <v-text-field
      v-model="search"
      label="Поиск"
      placeholder="Введите название для поиска"
      prepend-inner-icon="mdi-magnify"
      clearable
      density="comfortable"
      variant="outlined"
      hide-details
      class="catalog-tab__search"
    />

    <v-alert
      v-if="error"
      type="error"
      variant="tonal"
      title="Не удалось загрузить каталог"
      class="mb-4"
    >
      {{ error }}
      <div class="mt-3">
        <v-btn size="small" variant="outlined" @click="load()">Повторить</v-btn>
      </div>
    </v-alert>

    <v-data-table-server
      v-model:items-per-page="itemsPerPage"
      :page="page"
      :items="list"
      :headers="headers"
      :loading="loading"
      :items-length="pagination?.total ?? 0"
      item-value="id"
      @update:options="handleUpdateOptions"
    >
      <template #loading>
        <v-container fluid class="d-flex flex-column" min-height="240">
          <loading-placeholder size="large" />
        </v-container>
      </template>

      <template #[`item.createdAt`]="{ item }">
        {{ displayDate(rawOf<{ createdAt: string }>(item).createdAt) }}
      </template>

      <template #no-data>
        <div class="catalog-tab__empty">
          <NoDataPlaceholder
            text="В каталоге пока нет элементов"
            size="small"
          />
        </div>
      </template>
    </v-data-table-server>
  </div>
</template>

<style scoped>
  .catalog-tab__description {
    margin: 0 0 16px;
    font-size: 14px;
    line-height: 1.7;
  }

  .catalog-tab__search {
    max-width: 360px;
    margin-bottom: 16px;
  }

  .catalog-tab__empty {
    padding: 32px 16px;
  }
</style>
