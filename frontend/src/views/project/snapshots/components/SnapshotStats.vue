<script setup lang="ts">
  import { getObjectWord } from '@/utils/snapshots.ts'
  import type { DetectionStat } from '@/utils/snapshots.ts'

  defineOptions({ name: 'SnapshotStats' })

  interface Props {
    grouped: DetectionStat[]
    filteredCount: number
    threshold: number
    hoveredTechniqueId?: number | null
    selectedTechniqueId?: number | null
    hiddenTechniqueIds?: Set<number>
  }

  const props = withDefaults(defineProps<Props>(), {
    hoveredTechniqueId: null,
    selectedTechniqueId: null,
    hiddenTechniqueIds: () => new Set<number>()
  })

  const emit = defineEmits<{
    (e: 'hover', value: number | null): void
    (e: 'focus', value: number | null): void
    (e: 'select', value: number | null): void
    (e: 'toggle-hidden', value: number): void
  }>()

  function isHidden(techniqueId: number): boolean {
    return props.hiddenTechniqueIds.has(techniqueId)
  }
</script>

<template>
  <section class="snapshot-stats" aria-label="Распознанная техника">
    <div class="stats-heading">
      <h4>Распознанная техника</h4>
      <span>{{ filteredCount }}</span>
    </div>
    <p v-if="!grouped.length" class="stats-empty">
      Нет объектов с вероятностью ≥ {{ threshold }}%. Это не подтверждает их
      отсутствие на площадке.
    </p>
    <div v-if="grouped.length" class="stats-list">
      <div
        v-for="stat in grouped"
        :key="stat.techniqueId"
        class="stats-row-wrap"
        :class="{ 'stats-row-wrap--hidden': isHidden(stat.techniqueId) }"
      >
        <button
          type="button"
          class="stats-row"
          :class="{
            'stats-row--active':
              hoveredTechniqueId === stat.techniqueId ||
              selectedTechniqueId === stat.techniqueId
          }"
          :aria-pressed="selectedTechniqueId === stat.techniqueId"
          @mouseenter="emit('hover', stat.techniqueId)"
          @mouseleave="emit('hover', null)"
          @focus="emit('focus', stat.techniqueId)"
          @blur="emit('focus', null)"
          @click="
            emit(
              'select',
              selectedTechniqueId === stat.techniqueId ? null : stat.techniqueId
            )
          "
        >
          <span class="stats-name">
            <span class="stats-swatches" aria-hidden="true"
              ><span
                v-for="color in stat.colors"
                :key="color"
                class="stats-dot"
                :style="{ background: color }"
            /></span>
            <span>{{ stat.objectClass }}</span>
          </span>
          <span class="stats-count">{{ stat.count }}</span>
        </button>
        <v-btn
          :icon="isHidden(stat.techniqueId) ? 'mdi-eye-off' : 'mdi-eye'"
          variant="text"
          density="compact"
          size="small"
          class="stats-eye"
          :aria-label="
            isHidden(stat.techniqueId)
              ? `Показать ${stat.objectClass}`
              : `Скрыть ${stat.objectClass}`
          "
          :aria-pressed="isHidden(stat.techniqueId)"
          @click="emit('toggle-hidden', stat.techniqueId)"
        />
      </div>
    </div>
    <div v-if="grouped.length" class="stats-total">
      Всего:
      <strong>{{ filteredCount }} {{ getObjectWord(filteredCount) }}</strong>
    </div>
    <p v-if="grouped.length" class="stats-hint">
      <v-icon size="15">mdi-cursor-default-click-outline</v-icon> Выберите тип
      техники для подсветки на снимке, глаз — скрыть класс.
    </p>
  </section>
</template>

<style scoped>
  .snapshot-stats {
    width: 100%;
    padding: 20px;
    border: 1px solid #e0e7f0;
    border-radius: 12px;
    background: #ffffff;
  }
  .stats-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 16px;
  }
  .stats-heading h4 {
    font-size: 14px;
    font-weight: 650;
  }
  .stats-heading > span {
    font-size: 12px;
    background: #eef3f9;
    color: #506581;
    padding: 3px 8px;
    border-radius: 6px;
  }
  .stats-list {
    display: grid;
    gap: 6px;
  }
  .stats-row-wrap {
    display: flex;
    align-items: center;
    gap: 2px;
    padding-right: 4px;
    border: 1px solid transparent;
    border-radius: 8px;
    transition:
      background 180ms ease,
      border-color 180ms ease;
  }
  .stats-row-wrap:hover,
  .stats-row-wrap:has(.stats-row--active),
  .stats-row-wrap:has(.stats-row[aria-pressed='true']) {
    background: #f0f4fa;
    border-color: #dce5f2;
  }
  .stats-row-wrap:has(.stats-row[aria-pressed='true']) {
    border-color: #8aa9db;
  }
  .stats-row-wrap:has(.stats-row:focus-visible) {
    outline: 3px solid #2563eb;
    outline-offset: 2px;
  }
  .stats-row-wrap--hidden {
    opacity: 0.45;
  }
  .stats-row {
    background: transparent;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px;
    border: none;
    border-radius: 8px;
    text-align: left;
    color: #33455c;
    cursor: pointer;
    min-width: 0;
  }
  .stats-row:focus {
    outline: none;
  }
  .stats-name {
    display: flex;
    align-items: center;
    gap: 9px;
    font-size: 13px;
    min-width: 0;
  }
  .stats-name > span:last-child {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .stats-swatches {
    display: flex;
    align-items: center;
    gap: 3px;
    flex-shrink: 0;
  }
  .stats-dot {
    width: 10px;
    height: 10px;
    border: 1px solid #00000028;
    border-radius: 3px;
  }
  .stats-count {
    font-size: 13px;
    font-weight: 700;
  }
  .stats-eye {
    flex-shrink: 0;
    color: #8a9ab0;
  }
  .stats-eye[aria-pressed='true'] {
    color: #b45309;
  }
  .stats-total {
    border-top: 1px solid #e8edf3;
    padding-top: 14px;
    margin-top: 14px;
    font-size: 12px;
    color: #5f7188;
  }
  .stats-total strong {
    color: #33455c;
  }
  .stats-hint {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    margin-top: 14px;
    font-size: 12px;
    color: #5f7188;
    line-height: 1.6;
  }
  .stats-empty {
    font-size: 13px;
    color: #5f7188;
    line-height: 1.7;
  }
  @media (prefers-reduced-motion: reduce) {
    .stats-row {
      transition: none;
    }
  }
</style>
