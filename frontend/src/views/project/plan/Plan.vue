<script setup lang="ts">
  import { computed, onMounted, ref, watch } from 'vue'
  import { useRoute } from 'vue-router'
  import { useProjectPlanStore } from '@/store/plan.ts'
  import { useCatalogsStore } from '@/store/catalogs.ts'
  import {
    flattenVisible,
    generateDays,
    generateMonths,
    getInitialExpanded,
    getPlanBounds,
    getTotalTechnique,
    getTodayIndex
  } from '@/utils/plan.ts'
  import { GANTT_CELL_WIDTH } from '@/utils/plan.ts'
  import Gantt from './components/gantt/Gantt.vue'
  import MobileStageList from './components/MobileStageList.vue'
  import CreateEditStageDialog from './components/CreateEditStageDialog.vue'
  import StageTechniqueDialog from './components/StageTechniqueDialog.vue'
  import ConfirmDeleteStageDialog from './components/ConfirmDeleteStageDialog.vue'
  import type { Stage } from '@/types/plan'
  import type { WorkType } from '@/types/plan'
  import type { Technique } from '@/store/variants.ts'
  import type { PaginatedCatalog } from '@/types/catalogs'
  import type { DateString } from '@/types/api.ts'
  import LoadingPlaceholder from '@/components/LoadingPlaceholder.vue'
  import { displayDate } from '@/utils/datetime.ts'
  import { getApiErrorDetail } from '@/utils/errors.ts'

  const route = useRoute()
  const planStore = useProjectPlanStore()
  const catalogsStore = useCatalogsStore()

  const projectId = computed(() => {
    const raw = route.params.projectId
    return Array.isArray(raw) ? raw[0] : (raw as string)
  })

  const numericProjectId = computed(() => Number(projectId.value))

  const list = computed(() => planStore.getList)
  const stages = list
  const loading = computed(() => planStore.getLoadingState)
  const isLoading = computed(() => loading.value.list)
  const loadError = ref<string | null>(null)
  const plannedTechniqueCount = computed(() =>
    stages.value.reduce((total, stage) => total + getTotalTechnique(stage), 0)
  )
  const hasActualProgress = computed(() =>
    stages.value.some(
      (stage) => stage.actual !== null && stage.actual !== undefined
    )
  )
  const plannedDates = computed(() => ({
    start: stages.value.map((stage) => stage.startDate).sort()[0],
    end: stages.value
      .map((stage) => stage.endDate)
      .sort()
      .at(-1)
  }))

  const bounds = computed(() => getPlanBounds(stages.value))
  const days = computed(() => generateDays(bounds.value))
  const months = computed(() => generateMonths(days.value))
  const todayIndex = computed(() =>
    getTodayIndex(bounds.value.start, days.value)
  )
  const timelineWidth = computed(() => days.value.length * GANTT_CELL_WIDTH)

  const visibleStages = computed(() =>
    flattenVisible(stages.value, expanded.value)
  )

  const expanded = ref<Set<number>>(new Set())

  function toggleExpand(id: number) {
    const next = new Set(expanded.value)
    if (next.has(id)) {
      next.delete(id)
    } else {
      next.add(id)
    }
    expanded.value = next
  }

  function applyInitialExpanded() {
    if (!stages.value.length) return
    expanded.value = getInitialExpanded(stages.value)
  }

  const workTypesCatalog = ref<PaginatedCatalog<WorkType> | null>(null)
  const techniquesCatalog = ref<PaginatedCatalog<Technique> | null>(null)

  function ensureCatalogs(pid: string) {
    const workKey = `workTypes-${pid}`
    if (!catalogsStore.catalogs[workKey]) {
      catalogsStore.add(workKey, {
        url: `/projects/${pid}/work-types`,
        paginated: true,
        allowSearch: true
      })
    }
    workTypesCatalog.value = catalogsStore.create<WorkType>(
      workKey
    ) as PaginatedCatalog<WorkType>

    if (!catalogsStore.catalogs['techniques']) {
      catalogsStore.add('techniques', {
        url: '/techniques',
        paginated: true,
        allowSearch: true
      })
    }
    if (!techniquesCatalog.value) {
      techniquesCatalog.value = catalogsStore.create<Technique>(
        'techniques'
      ) as PaginatedCatalog<Technique>
    }
  }

  watch(
    projectId,
    (id) => {
      if (id) ensureCatalogs(id)
    },
    { immediate: true }
  )

  const showStageDialog = ref(false)
  const editingStage = ref<Stage | null>(null)
  const parentIdForCreate = ref<number | null>(null)
  const stageDialogLoading = ref(false)
  const stageDialogError = ref<string | null>(null)

  const showTechniqueDialog = ref(false)
  const techniqueStage = ref<Stage | null>(null)
  const techniqueDialogLoading = ref(false)
  const techniqueDialogError = ref<string | null>(null)

  const showDeleteDialog = ref(false)
  const deleteTarget = ref<Stage | null>(null)
  const deleteDialogLoading = ref(false)
  const deleteDialogError = ref<string | null>(null)

  function openCreateStage() {
    editingStage.value = null
    parentIdForCreate.value = null
    stageDialogError.value = null
    showStageDialog.value = true
  }

  function openCreateSubStage(stage: Stage) {
    editingStage.value = null
    parentIdForCreate.value = stage.id
    stageDialogError.value = null
    showStageDialog.value = true
  }

  function openEditStage(stage: Stage) {
    editingStage.value = stage
    parentIdForCreate.value = null
    stageDialogError.value = null
    showStageDialog.value = true
  }

  function openEditTechniques(stage: Stage) {
    techniqueStage.value = stage
    techniqueDialogError.value = null
    showTechniqueDialog.value = true
  }

  function openDeleteStage(stage: Stage) {
    deleteTarget.value = stage
    deleteDialogError.value = null
    showDeleteDialog.value = true
  }

  async function handleStageOk(data: {
    workTypeId: number
    startDate: string
    endDate: string
    parentId: number | null
    techniques: { name: string; quantity: number }[]
  }) {
    if (!projectId.value) return
    stageDialogLoading.value = true
    stageDialogError.value = null
    try {
      if (editingStage.value) {
        await planStore.updateItem(
          { projectId: numericProjectId.value, stageId: editingStage.value.id },
          {
            startDate: data.startDate as DateString,
            endDate: data.endDate as DateString,
            parentId: data.parentId,
            workTypeId: data.workTypeId
          }
        )
        if (data.techniques) {
          await planStore.updateTechniques(
            {
              projectId: numericProjectId.value,
              stageId: editingStage.value.id
            },
            { techniques: data.techniques }
          )
        }
      } else {
        await planStore.createItem(
          { projectId: numericProjectId.value },
          {
            startDate: data.startDate as DateString,
            endDate: data.endDate as DateString,
            parentId: data.parentId,
            workTypeId: data.workTypeId,
            techniques: data.techniques
          }
        )
        if (data.parentId && !expanded.value.has(data.parentId)) {
          const next = new Set(expanded.value)
          next.add(data.parentId)
          expanded.value = next
        }
      }
      showStageDialog.value = false
      editingStage.value = null
      parentIdForCreate.value = null
    } catch (e: unknown) {
      stageDialogError.value = getApiErrorDetail(e, 'Не удалось сохранить этап')
    } finally {
      stageDialogLoading.value = false
    }
  }

  function handleStageCancel() {
    showStageDialog.value = false
    editingStage.value = null
    parentIdForCreate.value = null
    stageDialogError.value = null
  }

  async function handleTechniqueOk(
    techniques: { name: string; quantity: number }[]
  ) {
    if (!projectId.value || !techniqueStage.value) return
    techniqueDialogLoading.value = true
    techniqueDialogError.value = null
    try {
      await planStore.updateTechniques(
        { projectId: numericProjectId.value, stageId: techniqueStage.value.id },
        { techniques }
      )
      showTechniqueDialog.value = false
      techniqueStage.value = null
    } catch (e: unknown) {
      techniqueDialogError.value = getApiErrorDetail(
        e,
        'Не удалось обновить технику'
      )
    } finally {
      techniqueDialogLoading.value = false
    }
  }

  function handleTechniqueCancel() {
    showTechniqueDialog.value = false
    techniqueStage.value = null
    techniqueDialogError.value = null
  }

  async function handleDeleteConfirm() {
    if (!projectId.value || !deleteTarget.value) return
    deleteDialogLoading.value = true
    deleteDialogError.value = null
    try {
      await planStore.deleteItem({
        projectId: numericProjectId.value,
        stageId: deleteTarget.value.id
      })
      showDeleteDialog.value = false
      deleteTarget.value = null
    } catch (e: unknown) {
      deleteDialogError.value = getApiErrorDetail(e, 'Не удалось удалить этап')
    } finally {
      deleteDialogLoading.value = false
    }
  }

  function handleDeleteCancel() {
    showDeleteDialog.value = false
    deleteTarget.value = null
    deleteDialogError.value = null
  }

  async function loadPlan(id = projectId.value) {
    if (!id) return
    loadError.value = null
    try {
      await planStore.loadList({ projectId: Number(id) })
      applyInitialExpanded()
    } catch (error: unknown) {
      loadError.value = getApiErrorDetail(error, 'Не удалось загрузить план')
    }
  }

  onMounted(() => {
    void loadPlan()
  })

  watch(projectId, async (id) => {
    if (id) {
      expanded.value = new Set()
      await loadPlan(id)
    }
  })

  watch(
    () => stages.value.length,
    () => {
      if (stages.value.length && expanded.value.size === 0) {
        applyInitialExpanded()
      }
    }
  )
</script>

<template>
  <section class="plan-intro bw-panel" aria-label="О календарном плане">
    <div>
      <div class="bw-eyebrow">Основа мониторинга</div>
      <h2>План работ и ресурсов</h2>
      <p class="bw-muted">
        Укажите сроки этапов и необходимую технику. Эти данные помогут сравнить
        происходящее на площадке с вашим планом.
      </p>
    </div>
    <div v-if="stages.length && !loadError && !isLoading" class="plan-summary">
      <span class="bw-chip"
        ><v-icon icon="mdi-layers-outline" size="16" />Этапов:
        {{ stages.length }}</span
      >
      <span class="bw-chip"
        ><v-icon icon="mdi-excavator" size="16" />{{
          plannedTechniqueCount
        }}
        ед. в требованиях</span
      >
    </div>
  </section>

  <div
    v-if="isLoading"
    class="bw-panel plan-state"
    role="status"
    aria-label="Загрузка календарного плана"
  >
    <loading-placeholder size="large" />
  </div>

  <section v-else-if="loadError" class="bw-panel plan-state" role="alert">
    <v-icon icon="mdi-cloud-alert-outline" size="40" color="error" />
    <h2>Не удалось загрузить план</h2>
    <p class="bw-muted">{{ loadError }}</p>
    <v-btn
      variant="tonal"
      color="primary"
      prepend-icon="mdi-refresh"
      @click="loadPlan()"
      >Повторить загрузку</v-btn
    >
  </section>

  <section v-else-if="!stages.length" class="bw-panel plan-state">
    <div class="plan-state__icon">
      <v-icon icon="mdi-calendar-plus-outline" size="34" />
    </div>
    <div class="bw-eyebrow">Первый шаг</div>
    <h2>Добавьте первый этап работ</h2>
    <p class="bw-muted">
      Начните с основного этапа, задайте сроки и технику. Позже можно добавить
      подэтапы и уточнить план.
    </p>
    <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateStage"
      >Добавить этап</v-btn
    >
  </section>

  <section v-else class="plan-content">
    <div class="plan-caption">
      <span
        >{{ displayDate(plannedDates.start) }} —
        {{ displayDate(plannedDates.end) }}</span
      >
      <div class="plan-legend">
        <span><i class="plan-legend__dot" />Этап</span>
        <span
          ><i class="plan-legend__dot plan-legend__dot--actual" />Фактическое
          выполнение</span
        >
        <span
          ><i class="plan-legend__dot plan-legend__dot--summary" />С
          подэтапами</span
        >
        <span
          ><i class="plan-legend__dot plan-legend__dot--today" />Сегодня</span
        >
      </div>
    </div>
    <div v-if="!hasActualProgress" class="plan-analytics-hint" role="status">
      <v-icon icon="mdi-chart-timeline-variant-shimmer" size="22" />
      <div>
        <strong>Фактическое выполнение пока не определено</strong>
        <span>
          Зелёная или цветная полоса появится в строке конечного этапа, когда
          анализ снимков сопоставит технику с планом. Ожидание не повысит score,
          если состав техники на снимках не соответствует плану этапа.
        </span>
      </div>
      <v-btn
        variant="text"
        color="primary"
        size="small"
        prepend-icon="mdi-refresh"
        @click="loadPlan()"
      >
        Обновить
      </v-btn>
    </div>
    <div class="plan-desktop">
      <Gantt
        :visible-stages="visibleStages"
        :stages="stages"
        :days="days"
        :months="months"
        :bounds="bounds"
        :today-index="todayIndex"
        :timeline-width="timelineWidth"
        :expanded="expanded"
        @create-stage="openCreateStage"
        @toggle-expand="toggleExpand"
        @add-sub-stage="openCreateSubStage"
        @edit-stage="openEditStage"
        @edit-techniques="openEditTechniques"
        @delete-stage="openDeleteStage"
      />
    </div>
    <MobileStageList
      class="plan-mobile"
      :visible-stages="visibleStages"
      :stages="stages"
      :expanded="expanded"
      @toggle-expand="toggleExpand"
      @add-sub-stage="openCreateSubStage"
      @edit-stage="openEditStage"
      @edit-techniques="openEditTechniques"
      @delete-stage="openDeleteStage"
    />
  </section>

  <CreateEditStageDialog
    v-if="workTypesCatalog && techniquesCatalog"
    :open="showStageDialog"
    :loading="stageDialogLoading"
    :error="stageDialogError"
    :project-id="numericProjectId"
    :stage="editingStage"
    :parent-id="parentIdForCreate"
    :work-types-catalog="workTypesCatalog"
    :techniques-catalog="techniquesCatalog"
    @ok="handleStageOk"
    @cancel="handleStageCancel"
  />

  <StageTechniqueDialog
    v-if="techniquesCatalog"
    :open="showTechniqueDialog"
    :loading="techniqueDialogLoading"
    :error="techniqueDialogError"
    :stage="techniqueStage"
    :techniques-catalog="techniquesCatalog"
    @ok="handleTechniqueOk"
    @cancel="handleTechniqueCancel"
  />

  <ConfirmDeleteStageDialog
    :open="showDeleteDialog"
    :loading="deleteDialogLoading"
    :error="deleteDialogError"
    :stage="deleteTarget"
    @confirm="handleDeleteConfirm"
    @cancel="handleDeleteCancel"
  />
</template>

<style scoped>
  .plan-intro {
    display: flex;
    justify-content: space-between;
    gap: 24px;
    padding: 24px;
    margin-bottom: 24px;
  }
  .plan-intro h2,
  .plan-state h2 {
    font-size: 20px;
    font-weight: 650;
    margin: 6px 0 8px;
  }
  .plan-intro p {
    margin: 0;
    max-width: 650px;
    line-height: 1.65;
  }
  .plan-summary {
    display: flex;
    flex-wrap: wrap;
    align-content: center;
    justify-content: flex-end;
    gap: 8px;
    max-width: 260px;
    flex-shrink: 0;
  }
  .plan-summary .bw-chip {
    display: inline-flex;
    align-items: center;
    gap: 7px;
  }
  .plan-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 64px 24px;
    text-align: center;
    min-height: 310px;
  }
  .plan-state p {
    max-width: 490px;
    margin: 0 0 12px;
    line-height: 1.65;
    overflow-wrap: anywhere;
  }
  .plan-state__icon {
    display: grid;
    place-items: center;
    width: 68px;
    height: 68px;
    color: #2563eb;
    background: #eff5ff;
    border-radius: 20px;
    margin-bottom: 8px;
  }
  .plan-content,
  .plan-desktop {
    min-width: 0;
    width: 100%;
  }
  .plan-analytics-hint {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
    padding: 12px 14px;
    border: 1px solid #d9e2ef;
    border-radius: 12px;
    background: #f8fafc;
    color: #53647a;
  }
  .plan-analytics-hint > div {
    display: grid;
    gap: 2px;
    flex: 1;
  }
  .plan-analytics-hint strong {
    color: #26374d;
    font-size: 13px;
  }
  .plan-analytics-hint span {
    font-size: 12px;
    line-height: 1.45;
  }
  .plan-caption {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    color: #53647a;
    font-size: 13px;
    margin-bottom: 14px;
  }
  .plan-legend,
  .plan-legend span {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  .plan-legend {
    gap: 16px;
  }
  .plan-legend__dot {
    width: 10px;
    height: 10px;
    background: #2563eb;
    border-radius: 3px;
  }
  .plan-legend__dot--summary {
    background: #0f766e;
  }

  .plan-legend__dot--actual {
    background: #10b981;
  }
  .plan-legend__dot--today {
    background: #f59e0b;
  }
  .plan-mobile {
    display: none;
  }
  @media (max-width: 1000px) {
    .plan-intro {
      flex-direction: column;
      gap: 16px;
    }
    .plan-summary {
      justify-content: flex-start;
      max-width: none;
    }
  }
  @media (max-width: 767px) {
    .plan-intro {
      padding: 20px;
      margin-bottom: 20px;
    }
    .plan-intro h2 {
      font-size: 18px;
    }
    .plan-desktop,
    .plan-legend {
      display: none;
    }
    .plan-mobile {
      display: grid;
    }
    .plan-state {
      padding: 40px 20px;
    }
  }
</style>
