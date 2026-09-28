<script setup lang="ts">
  import type { Stage } from '@/types/plan'
  import { GANTT_CELL_WIDTH, hasChildren } from '@/utils/plan.ts'
  import GanttBar from './GanttBar.vue'
  import { PLAN_ROW_HEIGHT } from './layout'

  defineProps<{
    visibleStages: Stage[]
    stages: Stage[]
    days: Date[]
    bounds: { start: Date; end: Date }
    todayIndex: number | null
    timelineWidth: number
  }>()
</script>

<template>
  <div class="gantt__timeline" :style="{ width: timelineWidth + 'px' }">
    <div
      v-if="todayIndex !== null"
      class="gantt__today"
      :style="{
        left: todayIndex * GANTT_CELL_WIDTH + 'px',
        width: GANTT_CELL_WIDTH + 'px'
      }"
    />
    <div class="gantt__grid">
      <div
        v-for="(_, idx) in days"
        :key="'v-' + idx"
        class="gantt__grid-line"
        :style="{ left: idx * GANTT_CELL_WIDTH + 'px' }"
        :class="{ 'gantt__grid-line--today': idx === todayIndex }"
      />
    </div>
    <div
      v-for="stage in visibleStages"
      :key="'bar-' + stage.id"
      class="gantt__row gantt__row--right"
      :style="{ height: PLAN_ROW_HEIGHT + 'px' }"
    >
      <GanttBar
        :stage="stage"
        :start="bounds.start"
        :is-summary="hasChildren(stages, stage.id)"
      />
    </div>
  </div>
</template>

<style scoped>
  .gantt__row {
    display: flex;
    align-items: center;
    border-bottom: 1px solid #edf1f6;
    position: relative;
  }

  .gantt__row--right {
    position: relative;
    border-bottom: 1px solid #edf1f6;
  }

  .gantt__timeline {
    position: relative;
    min-height: 100%;
  }

  .gantt__grid {
    position: absolute;
    inset: 0;
    pointer-events: none;
  }

  .gantt__grid-line {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 1px;
    background: #edf1f6;
  }

  .gantt__grid-line--today {
    background: rgba(245, 158, 11, 0.35);
  }

  .gantt__today {
    position: absolute;
    top: 0;
    bottom: 0;
    background: rgba(245, 158, 11, 0.09);
    pointer-events: none;
    z-index: 1;
  }
</style>
