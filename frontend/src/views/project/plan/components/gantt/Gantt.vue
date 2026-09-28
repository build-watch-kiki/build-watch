<script setup lang="ts">
  import { ref } from 'vue'
  import type { Stage } from '@/types/plan'
  import type { MonthSpan } from '@/utils/plan.ts'
  import GanttHeader from './GanttHeader.vue'
  import GanttTable from './GanttTable.vue'
  import GanttTimeline from './GanttTimeline.vue'

  defineProps<{
    visibleStages: Stage[]
    stages: Stage[]
    days: Date[]
    months: MonthSpan[]
    bounds: { start: Date; end: Date }
    todayIndex: number | null
    timelineWidth: number
    expanded: Set<number>
  }>()

  defineEmits<{
    createStage: []
    toggleExpand: [id: number]
    addSubStage: [stage: Stage]
    editStage: [stage: Stage]
    editTechniques: [stage: Stage]
    deleteStage: [stage: Stage]
  }>()

  const rightBodyRef = ref<HTMLElement | null>(null)
  const headerScrollLeft = ref(0)

  function onRightBodyScroll() {
    if (!rightBodyRef.value) return
    headerScrollLeft.value = rightBodyRef.value.scrollLeft
  }
</script>

<template>
  <div class="gantt" aria-label="Диаграмма календарного плана">
    <GanttHeader
      :months="months"
      :days="days"
      :today-index="todayIndex"
      :timeline-width="timelineWidth"
      :scroll-left="headerScrollLeft"
      @create="$emit('createStage')"
    />

    <div class="gantt__body">
      <GanttTable
        :visible-stages="visibleStages"
        :stages="stages"
        :expanded="expanded"
        @toggle-expand="$emit('toggleExpand', $event)"
        @add-sub-stage="$emit('addSubStage', $event)"
        @edit-stage="$emit('editStage', $event)"
        @edit-techniques="$emit('editTechniques', $event)"
        @delete-stage="$emit('deleteStage', $event)"
      />
      <div
        ref="rightBodyRef"
        class="gantt__right-body"
        tabindex="0"
        role="region"
        aria-label="Временная шкала этапов. Прокрутите для просмотра дат."
        @scroll="onRightBodyScroll"
      >
        <GanttTimeline
          :visible-stages="visibleStages"
          :stages="stages"
          :days="days"
          :bounds="bounds"
          :today-index="todayIndex"
          :timeline-width="timelineWidth"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
  .gantt {
    --gantt-table-width: clamp(440px, 48vw, 600px);
    border: 1px solid #e0e7f0;
    border-radius: 16px;
    overflow: hidden;
    width: 100%;
    min-width: 0;
    display: flex;
    flex-direction: column;
    background: #fff;
  }

  .gantt__body {
    display: flex;
    align-items: flex-start;
    min-width: 0;
  }

  .gantt__right-body {
    flex: 1;
    min-width: 0;
    overflow-x: auto;
    overflow-y: visible;
    position: relative;
    scrollbar-width: thin;
    scrollbar-color: #8aaaf0 #f1f5fb;
  }

  .gantt__right-body::-webkit-scrollbar {
    height: 8px;
  }

  .gantt__right-body::-webkit-scrollbar-track {
    background: #f1f5fb;
  }

  .gantt__right-body::-webkit-scrollbar-thumb {
    background: #8aaaf0;
    border-radius: 4px;
  }

  .gantt__right-body::-webkit-scrollbar-thumb:hover {
    background: #1565c0;
  }
</style>
