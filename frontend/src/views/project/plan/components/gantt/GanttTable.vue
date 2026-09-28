<script setup lang="ts">
  import type { Stage } from '@/types/plan'
  import { getDepth, hasChildren } from '@/utils/plan.ts'
  import { PLAN_ROW_HEIGHT } from './layout'
  import { displayDate } from '@/utils/datetime.ts'
  import TechniqueCell from './TechniqueCell.vue'

  defineProps<{
    visibleStages: Stage[]
    stages: Stage[]
    expanded: Set<number>
  }>()

  defineEmits<{
    toggleExpand: [id: number]
    addSubStage: [stage: Stage]
    editStage: [stage: Stage]
    editTechniques: [stage: Stage]
    deleteStage: [stage: Stage]
  }>()

  function isExpanded(id: number, expanded: Set<number>): boolean {
    return expanded.has(id)
  }

  function handleRowKeydown(event: KeyboardEvent) {
    if (event.target !== event.currentTarget) return
    ;(event.currentTarget as HTMLElement).click()
  }
</script>

<template>
  <div class="gantt__left-body">
    <div
      v-for="stage in visibleStages"
      :key="stage.id"
      class="gantt__row gantt__row--left"
      :style="{ height: PLAN_ROW_HEIGHT + 'px' }"
      role="button"
      tabindex="0"
      aria-label="Действия с этапом"
      @keydown.enter.space.prevent="handleRowKeydown"
    >
      <v-menu activator="parent" location="bottom">
        <v-list density="compact">
          <v-list-item
            prepend-icon="mdi-plus"
            title="Добавить подэтап"
            @click="$emit('addSubStage', stage)"
          />
          <v-list-item
            prepend-icon="mdi-pencil"
            title="Редактировать"
            @click="$emit('editStage', stage)"
          />
          <v-list-item
            prepend-icon="mdi-tools"
            title="Техника"
            @click="$emit('editTechniques', stage)"
          />
          <v-divider />
          <v-list-item
            prepend-icon="mdi-delete"
            title="Удалить"
            class="text-error"
            @click="$emit('deleteStage', stage)"
          />
        </v-list>
      </v-menu>
      <div class="gantt__td gantt__td--work">
        <span
          :style="{ width: getDepth(stage, stages) * 16 + 'px' }"
          class="gantt__indent"
        />
        <v-btn
          v-if="hasChildren(stages, stage.id)"
          :icon="
            isExpanded(stage.id, expanded)
              ? 'mdi-chevron-down'
              : 'mdi-chevron-right'
          "
          variant="text"
          density="compact"
          size="small"
          :aria-expanded="isExpanded(stage.id, expanded)"
          :aria-label="`${isExpanded(stage.id, expanded) ? 'Свернуть' : 'Развернуть'} подэтапы ${stage.workTypeName}`"
          class="gantt__expand"
          @click.stop="$emit('toggleExpand', stage.id)"
        />
        <span v-else class="gantt__expand-placeholder" />
        <span class="gantt__work-text" :title="stage.workTypeName">
          {{ stage.workTypeName }}
        </span>
        <v-tooltip text="Добавить подэтап" location="top">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              icon="mdi-plus-circle-outline"
              variant="text"
              density="compact"
              size="small"
              color="primary"
              class="gantt__add-sub"
              aria-label="Добавить подэтап"
              @click.stop="$emit('addSubStage', stage)"
            />
          </template>
        </v-tooltip>
      </div>
      <div class="gantt__td gantt__td--tech">
        <TechniqueCell :stage="stage" />
        <span
          v-if="stage.actual?.techniqueDeviationCount"
          class="gantt__actual-deviation"
          :title="stage.actual.message.text"
        >
          <v-icon size="13">mdi-alert-outline</v-icon>
          {{ stage.actual.techniqueDeviationCount }}
        </span>
      </div>
      <div class="gantt__td gantt__td--date">
        {{ displayDate(stage.startDate) }}
      </div>
      <div class="gantt__td gantt__td--date">
        {{ displayDate(stage.endDate) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
  .gantt__left-body {
    width: var(--gantt-table-width);
    min-width: var(--gantt-table-width);
    border-right: 1px solid #e0e7f0;
    overflow: visible;
  }

  .gantt__row {
    display: flex;
    align-items: center;
    border-bottom: 1px solid #edf1f6;
    position: relative;
  }

  .gantt__row--left {
    background: #fff;
    cursor: pointer;
    transition: background 0.15s;
  }

  .gantt__row--left:hover {
    background: rgba(var(--v-theme-primary), 0.06);
  }

  .gantt__row--left:focus-visible {
    outline: 2px solid rgb(var(--v-theme-primary));
    outline-offset: -2px;
  }

  .gantt__td {
    display: flex;
    align-items: center;
    padding: 0 8px;
    border-right: 1px solid #edf1f6;
    height: 100%;
    font-size: 13px;
    overflow: hidden;
    white-space: nowrap;
  }

  .gantt__td:last-child {
    border-right: none;
  }

  .gantt__td--work {
    flex: 1;
    min-width: 0;
    gap: 4px;
  }

  .gantt__td--tech {
    width: 84px;
    min-width: 84px;
    justify-content: center;
    color: #53647a;
    gap: 4px;
  }

  .gantt__actual-deviation {
    display: inline-flex;
    align-items: center;
    gap: 1px;
    color: #b45309;
    font-size: 10px;
    font-weight: 700;
  }

  .gantt__td--date {
    width: 86px;
    min-width: 86px;
    justify-content: center;
    font-size: 12px;
    color: #53647a;
  }

  .gantt__indent {
    flex-shrink: 0;
  }

  .gantt__expand {
    flex-shrink: 0;
    width: 32px !important;
    height: 32px !important;
  }

  .gantt__expand-placeholder {
    width: 32px;
    flex-shrink: 0;
  }

  .gantt__work-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
    min-width: 0;
  }

  .gantt__add-sub {
    flex-shrink: 0;
    opacity: 0;
    transition: opacity 0.15s;
  }

  .gantt__row--left:hover .gantt__add-sub,
  .gantt__add-sub:focus-visible {
    opacity: 1;
  }
</style>
