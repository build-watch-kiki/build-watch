<script setup lang="ts">
  import DataFormDialog from '@/components/DataFormDialog.vue'
  import type { CreateProjectPayload } from '@/types/projects.actions.ts'
  import { ref, watch } from 'vue'
  import type { DateString } from '@/types/api.ts'
  import { useCatalogsStore } from '@/store/catalogs.ts'
  import type { ProjectType } from '@/types/projects.ts'
  import CatalogSelector from '@/components/CatalogSelector.vue'

  interface Props {
    open: boolean
    loading: boolean
    error: string | null
  }

  const props = defineProps<Props>()

  const emit = defineEmits<{
    ok: [data: CreateProjectPayload]
    cancel: []
  }>()

  const catalogStore = useCatalogsStore()

  const projectTypesCatalog = catalogStore.create<ProjectType>('projectTypes')

  const today = new Date()

  const todayIso = today.toISOString().slice(0, 10) as DateString

  const tomorrow = new Date(today)
  tomorrow.setDate(today.getDate() + 1)

  const tomorrowIso = tomorrow.toISOString().slice(0, 10) as DateString

  const dataObject = ref<CreateProjectPayload>({
    name: '',
    type: null as unknown as string,
    startDate: todayIso,
    endDate: tomorrowIso
  })

  const resetForm = () => {
    dataObject.value = {
      name: '',
      type: null as unknown as string,
      startDate: todayIso,
      endDate: tomorrowIso
    }
  }

  const form = ref()

  const handleOk = async () => {
    const { valid } = await form.value.validate()

    if (!valid) {
      return
    }

    emit('ok', { ...dataObject.value })
  }

  const handleCancel = () => {
    emit('cancel')
    resetForm()
  }

  const nameRules = [
    (v: string) => !!v || 'Название обязательно',
    (v: string) => (v && v.trim().length >= 3) || 'Минимум 3 символа',
    (v: string) => (v && v.length <= 200) || 'Максимум 200 символов'
  ]

  const typeRules = [(v: string | number | null) => !!v || 'Тип обязателен']

  const startDateRules = [(v: string) => !!v || 'Дата начала обязательна']

  const endDateRules = [
    (v: string) => !!v || 'Дата окончания обязательна',
    (v: string) => {
      if (!v || !dataObject.value.startDate) return true
      return (
        v >= dataObject.value.startDate ||
        'Дата окончания не может быть раньше начала'
      )
    }
  ]
  watch(
    () => props.open,
    (open) => {
      if (!open) resetForm()
    }
  )
</script>

<template>
  <data-form-dialog
    :open="props.open"
    :data-object="dataObject"
    :labels="{
      title: 'Новый строительный объект',
      ok: 'Создать объект'
    }"
    :loading="props.loading"
    :error="props.error"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <v-form ref="form" @submit.prevent>
      <v-text-field
        v-model="dataObject.name"
        label="Название проекта"
        :rules="nameRules"
        variant="outlined"
        density="comfortable"
        class="mb-3"
        :disabled="props.loading"
      />

      <CatalogSelector
        v-model="dataObject.type"
        :catalog="projectTypesCatalog"
        :allow-search="true"
        item-value="name"
        item-title="name"
        label="Тип проекта"
        :placeholder="'Выберите тип проекта'"
        :rules="typeRules"
        :disabled="props.loading"
        :clearable="false"
        class="mb-3"
      />

      <v-text-field
        v-model="dataObject.startDate"
        label="Дата начала"
        type="date"
        :rules="startDateRules"
        variant="outlined"
        density="comfortable"
        class="mb-3"
        :disabled="props.loading"
      />

      <v-text-field
        v-model="dataObject.endDate"
        label="Дата окончания"
        type="date"
        :rules="endDateRules"
        variant="outlined"
        density="comfortable"
        :disabled="props.loading"
      />
    </v-form>
  </data-form-dialog>
</template>
