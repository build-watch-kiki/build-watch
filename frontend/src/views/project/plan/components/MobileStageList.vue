<script setup lang="ts">
  import type { Stage } from '@/types/plan'
  import { getDepth, hasChildren } from '@/utils/plan.ts'
  import { displayDate } from '@/utils/datetime.ts'
  import TechniqueCell from './gantt/TechniqueCell.vue'

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
</script>

<template>
  <div class="mobile-stages" aria-label="Этапы календарного плана">
    <article
      v-for="stage in visibleStages"
      :key="stage.id"
      class="mobile-stage bw-panel"
      :class="{ 'mobile-stage--child': getDepth(stage, stages) > 0 }"
      :style="{ marginLeft: Math.min(getDepth(stage, stages), 3) * 10 + 'px' }"
    >
      <div class="mobile-stage__heading">
        <v-btn
          v-if="hasChildren(stages, stage.id)"
          :icon="
            expanded.has(stage.id) ? 'mdi-chevron-down' : 'mdi-chevron-right'
          "
          :aria-label="`${expanded.has(stage.id) ? 'Свернуть' : 'Развернуть'} подэтапы ${stage.workTypeName}`"
          :aria-expanded="expanded.has(stage.id)"
          size="small"
          variant="tonal"
          color="primary"
          @click="$emit('toggleExpand', stage.id)"
        />
        <div class="mobile-stage__name">
          <span class="bw-eyebrow">{{
            getDepth(stage, stages) > 0 ? 'Подэтап' : 'Этап'
          }}</span>
          <h3>{{ stage.workTypeName }}</h3>
        </div>
        <v-menu location="bottom end">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              icon="mdi-dots-vertical"
              variant="text"
              size="small"
              :aria-label="`Действия с этапом ${stage.workTypeName}`"
            />
          </template>
          <v-list density="comfortable">
            <v-list-item
              prepend-icon="mdi-plus"
              title="Добавить подэтап"
              @click="$emit('addSubStage', stage)"
            />
            <v-list-item
              prepend-icon="mdi-pencil-outline"
              title="Редактировать этап"
              @click="$emit('editStage', stage)"
            />
            <v-list-item
              prepend-icon="mdi-excavator"
              title="Требования к технике"
              @click="$emit('editTechniques', stage)"
            />
            <v-divider />
            <v-list-item
              prepend-icon="mdi-trash-can-outline"
              title="Удалить этап"
              class="text-error"
              @click="$emit('deleteStage', stage)"
            />
          </v-list>
        </v-menu>
      </div>
      <dl class="mobile-stage__dates">
        <div>
          <dt>Начало</dt>
          <dd>{{ displayDate(stage.startDate) }}</dd>
        </div>
        <v-icon icon="mdi-arrow-right" size="16" aria-hidden="true" />
        <div>
          <dt>Окончание</dt>
          <dd>{{ displayDate(stage.endDate) }}</dd>
        </div>
      </dl>
      <div class="mobile-stage__footer">
        <div>
          <v-icon icon="mdi-excavator" size="18" /><span>Техника</span
          ><TechniqueCell :stage="stage" />
        </div>
        <v-btn
          variant="text"
          color="primary"
          size="small"
          prepend-icon="mdi-pencil-outline"
          @click="$emit('editStage', stage)"
          >Изменить</v-btn
        >
      </div>
      <div
        v-if="stage.actual"
        class="mobile-stage__actual"
        :class="`tone-${stage.actual.status}`"
      >
        <v-icon size="16">mdi-chart-timeline-variant</v-icon>
        <span>
          Факт: {{ displayDate(stage.actual.startDate) }} —
          {{ displayDate(stage.actual.endDate) }} ·
          {{ stage.actual.message.text }}
        </span>
      </div>
    </article>
  </div>
</template>

<style scoped>
  .mobile-stages {
    gap: 12px;
    min-width: 0;
  }
  .mobile-stage {
    padding: 16px;
    min-width: 0;
  }
  .mobile-stage--child {
    border-left: 3px solid #bfd3fb;
  }
  .mobile-stage__heading {
    display: flex;
    align-items: flex-start;
    gap: 10px;
  }
  .mobile-stage__name {
    flex: 1;
    min-width: 0;
  }
  .mobile-stage h3 {
    font-size: 15px;
    line-height: 1.5;
    font-weight: 650;
    margin: 3px 0 0;
    overflow-wrap: anywhere;
  }
  .mobile-stage__dates {
    display: flex;
    align-items: center;
    gap: 18px;
    background: #f4f7fb;
    border-radius: 10px;
    padding: 12px;
    margin: 16px 0 8px;
  }
  .mobile-stage__dates dt {
    color: #53647a;
    font-size: 11px;
    margin-bottom: 4px;
  }
  .mobile-stage__dates dd {
    font-size: 13px;
    font-weight: 600;
    margin: 0;
  }
  .mobile-stage__footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
  }

  .mobile-stage__actual {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    margin-top: 10px;
    padding: 8px 10px;
    border-radius: 8px;
    background: #ecfdf5;
    color: #047857;
    font-size: 12px;
    line-height: 1.45;
  }

  .mobile-stage__actual.tone-behind {
    background: #fff7ed;
    color: #b45309;
  }

  .mobile-stage__actual.tone-ahead {
    background: #f0f9ff;
    color: #0369a1;
  }

  .mobile-stage__actual.tone-unknown {
    background: #f1f5f9;
    color: #64748b;
  }
  .mobile-stage__footer > div {
    display: flex;
    align-items: center;
    gap: 7px;
    color: #53647a;
    font-size: 12px;
  }
</style>
