<script setup lang="ts">
  import { computed, ref, watch } from 'vue'
  import DataFormDialog from '@/components/DataFormDialog.vue'
  import CatalogSelector from '@/components/CatalogSelector.vue'
  import type { Stage } from '@/types/plan'
  import type { PaginatedCatalog } from '@/types/catalogs'
  import type { WorkType } from '@/types/plan'
  import type { Technique } from '@/store/variants'
  import { useProjectPlanStore } from '@/store/plan'
  import { useProjectsStore } from '@/store/projects'
  import type { CreateStagePayload } from '@/types/plan.actions'
  import type { DateString } from '@/types/api.ts'
  import NoDataPlaceholder from '@/components/NoDataPlaceholder.vue'

  interface Props {
    open: boolean
    loading: boolean
    error: string | null
    projectId: number
    stage?: Stage | null
    parentId?: number | null
    workTypesCatalog: PaginatedCatalog<WorkType>
    techniquesCatalog: PaginatedCatalog<Technique>
  }

  const props = withDefaults(defineProps<Props>(), {
    stage: null,
    parentId: null
  })

  const emit = defineEmits<{
    ok: [payload: CreateStagePayload]
    cancel: []
  }>()

  const planStore = useProjectPlanStore()
  const projectsStore = useProjectsStore()

  const currentProject = computed(() => projectsStore.detail)

  const todayIso = new Date()
    .toISOString()
    .slice(0, 10) as `${number}-${number}-${number}`

  const isEdit = computed(() => !!props.stage)

  const title = computed(() =>
    isEdit.value
      ? 'Редактировать этап'
      : props.parentId
        ? 'Добавить подэтап'
        : 'Добавить этап'
  )

  interface TechniqueRow {
    name: string | null
    quantity: number
  }

  const workTypeId = ref<number | null>(null)
  const startDate = ref('')
  const endDate = ref('')
  const techniques = ref<TechniqueRow[]>([])

  const formRef = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(
    null
  )

  const parentStage = computed(() => {
    const pid = props.parentId ?? props.stage?.parentId ?? null
    return pid ? planStore.getStageById(pid) : null
  })

  const workTypeSelectedItem = computed(() => {
    if (!props.stage?.workTypeId) return null
    return {
      id: props.stage.workTypeId,
      name: props.stage.workTypeName,
      createdAt: props.stage.createdAt
    } as WorkType
  })

  const startDateRules = [
    (v: string) => !!v || 'Дата начала обязательна',
    (v: string) => {
      if (!v || !parentStage.value?.startDate) return true
      return (
        v >= parentStage.value.startDate ||
        'Дата начала не может быть раньше даты начала родительского этапа'
      )
    },
    (v: string) => {
      if (!v || !currentProject.value?.startDate) return true
      return (
        v >= currentProject.value.startDate ||
        'Дата начала не может быть раньше даты начала проекта'
      )
    }
  ]

  const endDateRules = [
    (v: string) => !!v || 'Дата окончания обязательна',
    (v: string) => {
      if (!v || !startDate.value) return true
      return (
        v >= startDate.value || 'Дата окончания не может быть раньше начала'
      )
    },
    (v: string) => {
      if (!v || !parentStage.value?.endDate) return true
      return (
        v <= parentStage.value.endDate ||
        'Дата окончания не может быть позже даты окончания родительского этапа'
      )
    },
    (v: string) => {
      if (!v || !currentProject.value?.endDate) return true
      return (
        v <= currentProject.value.endDate ||
        'Дата окончания не может быть позже даты окончания проекта'
      )
    }
  ]

  const dataObject = computed(() => ({
    workTypeId: workTypeId.value,
    startDate: startDate.value,
    endDate: endDate.value,
    techniques: techniques.value
  }))

  function resetForm() {
    if (props.stage) {
      workTypeId.value = props.stage.workTypeId ?? null
      startDate.value = props.stage.startDate || todayIso
      endDate.value = props.stage.endDate || todayIso
      techniques.value = (props.stage.requiresTechnique || []).map((r) => ({
        name: r.name,
        quantity: r.quantity
      }))
    } else {
      workTypeId.value = null
      techniques.value = []
      const pid = props.parentId ?? null
      if (pid) {
        const parent = planStore.getStageById(pid)
        if (parent) {
          const siblings = planStore.getList.filter(
            (stage) => stage.parentId === pid
          )
          const prevEnd =
            siblings.length > 0
              ? siblings
                  .map((stage) => stage.endDate)
                  .sort()
                  .at(-1)
              : undefined
          if (prevEnd && prevEnd < parent.endDate) {
            const start = new Date(`${prevEnd}T00:00:00Z`)
            start.setUTCDate(start.getUTCDate() + 1)
            startDate.value = start.toISOString().slice(0, 10) as DateString
            const end = new Date(start)
            end.setUTCDate(end.getUTCDate() + 1)
            endDate.value = end.toISOString().slice(0, 10) as DateString
          } else {
            startDate.value = parent.startDate
            const end = new Date(parent.startDate)
            end.setDate(end.getDate() + 1)
            endDate.value = end.toISOString().slice(0, 10)
          }
        } else {
          startDate.value = todayIso
          endDate.value = todayIso
        }
      } else {
        if (currentProject.value) {
          startDate.value = currentProject.value.startDate
          const end = new Date(currentProject.value.startDate)
          end.setDate(end.getDate() + 1)
          endDate.value = end.toISOString().slice(0, 10)
        } else {
          startDate.value = todayIso
          endDate.value = todayIso
        }
      }
    }
  }

  watch(
    () => props.open,
    (open) => {
      if (open) resetForm()
    }
  )

  function updateQuantity(
    row: {
      name: string | null
      quantity: number
    },
    value: unknown
  ) {
    const quantity = Number(value)

    row.quantity = Number.isFinite(quantity)
      ? Math.max(1, Math.trunc(quantity))
      : 1
  }

  function addTechniqueRow() {
    techniques.value.push({ name: null, quantity: 1 })
  }

  function removeTechniqueRow(index: number) {
    techniques.value.splice(index, 1)
  }

  async function handleOk() {
    const result = await formRef.value?.validate()
    if (!result?.valid) return
    const filteredTechniques = techniques.value
      .filter((t) => t.name && t.name.trim() && t.quantity > 0)
      .map((t) => ({ name: t.name!.trim(), quantity: Number(t.quantity) }))
    const parentId = props.stage
      ? props.stage.parentId || null
      : (props.parentId ?? null)
    emit('ok', {
      startDate: startDate.value as `${number}-${number}-${number}`,
      endDate: endDate.value as `${number}-${number}-${number}`,
      parentId,
      workTypeId: workTypeId.value ?? 0,
      techniques: filteredTechniques
    } as CreateStagePayload)
  }

  function handleCancel() {
    emit('cancel')
  }
</script>

<template>
  <DataFormDialog
    :open="props.open"
    :loading="props.loading"
    :error="props.error"
    :data-object="dataObject as unknown as Record<string, unknown>"
    :labels="{ title: title }"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <v-form ref="formRef" class="stage-form" @submit.prevent>
      <p class="bw-muted stage-form__intro">
        Задайте вид работы, сроки выполнения и требования к технике.
      </p>
      <CatalogSelector
        v-model="workTypeId"
        :catalog="props.workTypesCatalog"
        :selected-item="workTypeSelectedItem"
        label="Вид работы"
        placeholder="Выберите вид работы"
        :rules="[]"
        :disabled="props.loading"
        :allow-search="true"
        :clearable="false"
        item-value="id"
        item-title="name"
        class="mb-3"
      />

      <div class="stage-form__dates">
        <v-text-field
          v-model="startDate"
          label="Дата начала"
          type="date"
          :rules="startDateRules"
          variant="outlined"
          density="comfortable"
          :disabled="props.loading"
        />

        <v-text-field
          v-model="endDate"
          label="Дата окончания"
          type="date"
          :rules="endDateRules"
          variant="outlined"
          density="comfortable"
          :disabled="props.loading"
        />
      </div>
      <div class="stage-form__section">
        <h3>Требования к технике</h3>
        <span class="bw-muted">На период этапа</span>
      </div>

      <no-data-placeholder v-if="techniques.length === 0" size="small">
        Техника пока не добавлена. Укажите машины, необходимые для выполнения
        работ.
      </no-data-placeholder>

      <v-row
        v-for="(row, idx) in techniques"
        :key="idx"
        no-gutters
        class="d-flex align-center stage-form__technique"
      >
        <v-col cols="12" sm="8">
          <CatalogSelector
            v-model="row.name"
            :catalog="props.techniquesCatalog"
            :selected-item="
              row.name
                ? ({
                    name: row.name,
                    nameRu:
                      props.stage?.requiresTechnique.find(
                        (r) => r.name === row.name
                      )?.nameRu || row.name,
                    id: 0,
                    createdAt: '' as unknown as string
                  } as unknown as Technique)
                : null
            "
            placeholder="Выберите технику"
            :disabled="props.loading"
            :allow-search="true"
            :clearable="false"
            item-value="name"
            item-title="nameRu"
            class="flex-grow-1"
          />
        </v-col>
        <v-col cols="10" sm="3">
          <v-text-field
            :model-value="row.quantity"
            type="number"
            label="Количество"
            variant="outlined"
            density="comfortable"
            class="stage-form__quantity"
            min="1"
            step="1"
            :disabled="props.loading"
            @update:model-value="updateQuantity(row, $event)"
          />
        </v-col>
        <v-col cols="2" sm="1" class="text-right">
          <v-btn
            icon="mdi-close"
            :aria-label="`Убрать технику из строки ${idx + 1}`"
            variant="text"
            class="mb-6"
            :disabled="props.loading"
            @click="removeTechniqueRow(idx)"
          />
        </v-col>
      </v-row>
    </v-form>
    <template #actions>
      <v-btn
        variant="tonal"
        color="primary"
        prepend-icon="mdi-plus"
        :disabled="props.loading"
        @click="addTechniqueRow"
      >
        Добавить технику
      </v-btn>
    </template>
  </DataFormDialog>
</template>

<style scoped>
  .stage-form__intro {
    margin: 0 0 20px;
    font-size: 13px;
    line-height: 1.6;
  }
  .stage-form__dates {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  .stage-form__section {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin: 12px 0 16px;
  }
  .stage-form__section h3 {
    font-size: 15px;
    font-weight: 650;
  }
  .stage-form__section span {
    font-size: 12px;
  }
  .stage-form__technique {
    border-top: 1px solid #e0e7f0;
    padding-top: 16px;
  }
  .stage-form__quantity {
    padding-left: 12px;
  }
  @media (max-width: 599px) {
    .stage-form__dates {
      grid-template-columns: 1fr;
      gap: 0;
    }
    .stage-form__quantity {
      padding-left: 0;
    }
    .stage-form__section {
      flex-wrap: wrap;
    }
  }
</style>
