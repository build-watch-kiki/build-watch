<script setup lang="ts">
  import { computed } from 'vue'
  import type { Stage } from '@/types/plan'
  import {
    GANTT_CELL_WIDTH,
    getBarStyle,
    getPeriodBarStyle
  } from '@/utils/plan.ts'
  import { displayDate } from '@/utils/datetime.ts'

  const props = defineProps<{
    stage: Stage
    start: Date
    isSummary: boolean
  }>()

  const statusLabels = {
    ahead: 'Опережение',
    on_track: 'По плану',
    behind: 'Отставание',
    unknown: 'Нет оценки'
  }

  const statusIcons = {
    ahead: 'mdi-trending-up',
    on_track: 'mdi-check-circle-outline',
    behind: 'mdi-trending-down',
    unknown: 'mdi-help-circle-outline'
  }

  const deviationBadge = computed(() => {
    const days = props.stage.actual?.deviationDays
    if (days === null || days === undefined || days === 0) return null
    return `${days < 0 ? '−' : '+'}${Math.abs(days)} дн.`
  })

  const deviationDescription = computed(() => {
    const days = props.stage.actual?.deviationDays
    if (days === null || days === undefined) return 'Отклонение пока не рассчитано'
    if (days < 0) return `Опережение на ${Math.abs(days)} дн.`
    if (days > 0) return `Отставание на ${days} дн.`
    return 'Выполняется по плану'
  })
</script>

<template>
  <div
    class="gantt__bar gantt__bar--plan"
    :class="{ 'gantt__bar--summary': isSummary }"
    :style="{
      left: getBarStyle(stage, start, GANTT_CELL_WIDTH).left,
      width: getBarStyle(stage, start, GANTT_CELL_WIDTH).width
    }"
    :title="`${stage.workTypeName}: ${displayDate(stage.startDate)} — ${displayDate(stage.endDate)}`"
  />
  <v-menu
    v-if="stage.actual"
    open-on-hover
    open-on-focus
    :close-on-content-click="false"
    location="top center"
    offset="8"
  >
    <template #activator="{ props: activatorProps }">
      <div
        v-bind="activatorProps"
        class="gantt__bar gantt__bar--actual"
        :class="`gantt__bar--${stage.actual.status}`"
        :style="{
          left: getPeriodBarStyle(
            stage.actual.startDate,
            stage.actual.endDate,
            start,
            GANTT_CELL_WIDTH
          ).left,
          width: getPeriodBarStyle(
            stage.actual.startDate,
            stage.actual.endDate,
            start,
            GANTT_CELL_WIDTH
          ).width
        }"
        role="button"
        tabindex="0"
        :aria-label="`${statusLabels[stage.actual.status]}. ${stage.actual.message.text}`"
      >
        <span v-if="deviationBadge" class="gantt__bar-badge">
          <v-icon size="11">{{ statusIcons[stage.actual.status] }}</v-icon>
          {{ deviationBadge }}
        </span>
      </div>
    </template>
    <v-card class="gantt-popover" elevation="8">
      <div
        class="gantt-popover__status"
        :class="`gantt-popover__status--${stage.actual.status}`"
      >
        <v-icon size="18">{{ statusIcons[stage.actual.status] }}</v-icon>
        <strong>{{ statusLabels[stage.actual.status] }}</strong>
      </div>
      <dl>
        <div>
          <dt>План</dt>
          <dd>
            {{ displayDate(stage.startDate) }} — {{ displayDate(stage.endDate) }}
          </dd>
        </div>
        <div>
          <dt>Факт</dt>
          <dd>
            {{ displayDate(stage.actual.startDate) }} —
            {{ displayDate(stage.actual.endDate) }}
          </dd>
        </div>
        <div>
          <dt>Сроки</dt>
          <dd>{{ deviationDescription }}</dd>
        </div>
        <div>
          <dt>Техника</dt>
          <dd>
            {{
              stage.actual.techniqueDeviationCount
                ? `Отклонения по ${stage.actual.techniqueDeviationCount} видам`
                : 'Без отклонений'
            }}
          </dd>
        </div>
      </dl>
      <p>{{ stage.actual.message.text }}</p>
    </v-card>
  </v-menu>
</template>

<style scoped>
  .gantt__bar {
    position: absolute;
    z-index: 2;
  }

  .gantt__bar--plan {
    top: 7px;
    height: 20px;
    background: #2563eb;
    border-radius: 6px;
    border: 1px solid #1d4ed8;
    box-shadow: 0 2px 4px #2563eb20;
  }

  .gantt__bar--summary {
    background: #0f766e;
    border-color: #0f766e;
    box-shadow: 0 2px 4px #0f766e20;
  }

  .gantt__bar--actual {
    --actual-color: #16a34a;
    --actual-border: #15803d;
    --actual-soft: #dcfce7;
    --actual-text: #166534;
    top: 33px;
    height: 9px;
    min-width: 8px;
    border-radius: 999px;
    border: 1px solid var(--actual-border);
    background: var(--actual-color);
    z-index: 3;
    cursor: help;
    outline: none;
    box-shadow: 0 1px 3px color-mix(in srgb, var(--actual-color) 35%, transparent);
  }

  .gantt__bar--actual:focus-visible {
    box-shadow: 0 0 0 3px var(--actual-soft);
  }

  .gantt__bar--ahead {
    --actual-color: #06b6d4;
    --actual-border: #0891b2;
    --actual-soft: #cffafe;
    --actual-text: #0e7490;
  }

  .gantt__bar--on_track {
    --actual-color: #22c55e;
    --actual-border: #16a34a;
    --actual-soft: #dcfce7;
    --actual-text: #166534;
  }

  .gantt__bar--behind {
    --actual-color: #f97316;
    --actual-border: #ea580c;
    --actual-soft: #ffedd5;
    --actual-text: #c2410c;
  }

  .gantt__bar--unknown {
    --actual-color: #94a3b8;
    --actual-border: #64748b;
    --actual-soft: #f1f5f9;
    --actual-text: #475569;
  }

  .gantt__bar-badge {
    position: absolute;
    left: 100%;
    top: 50%;
    display: inline-flex;
    align-items: center;
    gap: 2px;
    transform: translate(3px, -50%);
    padding: 2px 5px;
    border: 1px solid color-mix(in srgb, var(--actual-color) 45%, white);
    border-radius: 999px;
    background: var(--actual-soft);
    color: var(--actual-text);
    font-size: 9px;
    font-weight: 700;
    line-height: 12px;
    white-space: nowrap;
  }

  .gantt-popover {
    width: min(320px, calc(100vw - 32px));
    padding: 14px;
    border-radius: 12px;
  }

  .gantt-popover__status {
    display: flex;
    align-items: center;
    gap: 7px;
    margin-bottom: 12px;
    color: #166534;
  }

  .gantt-popover__status--ahead {
    color: #0e7490;
  }

  .gantt-popover__status--behind {
    color: #c2410c;
  }

  .gantt-popover__status--unknown {
    color: #475569;
  }

  .gantt-popover dl {
    display: grid;
    gap: 7px;
    margin: 0;
  }

  .gantt-popover dl > div {
    display: grid;
    grid-template-columns: 64px minmax(0, 1fr);
    gap: 10px;
    font-size: 12px;
  }

  .gantt-popover dt {
    color: #718198;
  }

  .gantt-popover dd {
    margin: 0;
    color: #26374d;
    font-weight: 600;
  }

  .gantt-popover p {
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid #e4eaf2;
    color: #53647a;
    font-size: 12px;
    line-height: 1.5;
  }
</style>
