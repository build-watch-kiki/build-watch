<script setup lang="ts">
  import { ref, watch } from 'vue'
  import type { MonthSpan } from '@/utils/plan.ts'
  import { GANTT_CELL_WIDTH } from '@/utils/plan.ts'

  const props = defineProps<{
    months: MonthSpan[]
    days: Date[]
    todayIndex: number | null
    timelineWidth: number
    scrollLeft?: number
  }>()

  const rightHeaderRef = ref<HTMLElement | null>(null)

  watch(
    () => props.scrollLeft,
    (value) => {
      if (rightHeaderRef.value && value !== undefined) {
        rightHeaderRef.value.scrollLeft = value
      }
    }
  )

  const emit = defineEmits<{ create: [] }>()
</script>

<template>
  <div class="gantt__header">
    <div class="gantt__left-header">
      <div class="gantt__th gantt__th--work">
        Вид работы
        <v-tooltip text="Добавить этап" location="top">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              variant="text"
              rounded="circle"
              color="primary"
              size="32"
              icon="mdi-plus-circle"
              @click="emit('create')"
            />
          </template>
        </v-tooltip>
      </div>
      <div class="gantt__th gantt__th--tech">Техника</div>
      <div class="gantt__th gantt__th--date">Начало</div>
      <div class="gantt__th gantt__th--date">Конец</div>
    </div>
    <div ref="rightHeaderRef" class="gantt__right-header">
      <div class="gantt__months" :style="{ width: timelineWidth + 'px' }">
        <div
          v-for="m in months"
          :key="m.key"
          class="gantt__month"
          :style="{ width: m.span * GANTT_CELL_WIDTH + 'px' }"
        >
          <span class="gantt__month-label">{{ m.label }}</span>
        </div>
      </div>
      <div class="gantt__days" :style="{ width: timelineWidth + 'px' }">
        <div
          v-for="(day, idx) in days"
          :key="idx"
          class="gantt__day"
          :style="{ width: GANTT_CELL_WIDTH + 'px' }"
          :class="{ 'gantt__day--today': idx === todayIndex }"
        >
          {{ day.getDate() }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .gantt__header {
    display: flex;
    border-bottom: 1px solid #e0e7f0;
    background: #f8fafc;
    font-size: 14px;
    font-weight: 600;
    color: #53647a;
    z-index: 3;
  }

  .gantt__left-header {
    display: flex;
    width: var(--gantt-table-width);
    min-width: var(--gantt-table-width);
    border-right: 1px solid #e0e7f0;
  }

  .gantt__th {
    display: flex;
    align-items: center;
    padding: 0 8px;
    border-right: 1px solid #e0e7f0;
    height: 56px;
  }

  .gantt__th:last-child {
    border-right: none;
  }

  .gantt__th--work {
    flex: 1;
    min-width: 0;
    padding: 0 16px 0;
  }

  .gantt__th--tech {
    width: 84px;
    min-width: 84px;
    justify-content: center;
  }

  .gantt__th--date {
    width: 86px;
    min-width: 86px;
    justify-content: center;
  }

  .gantt__right-header {
    flex: 1;
    min-width: 0;
    overflow-x: hidden;
    overflow-y: hidden;
  }

  .gantt__months {
    display: flex;
    height: 28px;
    border-bottom: 1px solid #e0e7f0;
  }

  .gantt__month {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    border-right: 1px solid #e0e7f0;
    font-weight: 600;
    white-space: nowrap;
    background: #f8fafc;
    font-size: 12px;
  }

  .gantt__month-label {
    position: sticky;
    left: 8px;
    padding: 0 8px;
  }

  .gantt__days {
    display: flex;
    height: 28px;
  }

  .gantt__day {
    display: flex;
    align-items: center;
    justify-content: center;
    border-right: 1px solid #edf1f6;
    font-size: 12px;
    font-weight: 400;
    color: #53647a;
  }

  .gantt__day--today {
    background: #fef3c7;
    font-weight: 700;
    color: #92400e;
  }

  .gantt__right-header {
    overflow: hidden;
  }
</style>
