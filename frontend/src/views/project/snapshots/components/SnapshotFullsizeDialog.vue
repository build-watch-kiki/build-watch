<script setup lang="ts">
  import type { Snapshot, SnapshotDetection } from '@/types/snapshots'
  import type { DetectionStat } from '@/utils/snapshots.ts'

  import SnapshotImageOverlay from './SnapshotImageOverlay.vue'
  import SnapshotStats from './SnapshotStats.vue'
  import SnapshotThresholdSlider from './SnapshotThresholdSlider.vue'

  interface Props {
    open: boolean
    snapshot: Snapshot
    filteredDetections: SnapshotDetection[]
    grouped: DetectionStat[]
    threshold: number
    hoveredTechniqueId?: number | null
    hiddenTechniqueIds?: Set<number>
  }

  const props = withDefaults(defineProps<Props>(), {
    hoveredTechniqueId: null,
    hiddenTechniqueIds: () => new Set<number>()
  })

  const emit = defineEmits<{
    'update:open': [value: boolean]
    hover: [techniqueId: number | null]
    'toggle-hidden': [techniqueId: number]
    'update:threshold': [value: number]
  }>()

  function handleClose() {
    emit('update:open', false)
  }
</script>

<template>
  <v-dialog
    :model-value="props.open"
    width="auto"
    max-width="95vw"
    content-class="snapshot-fullsize-dialog"
    @update:model-value="emit('update:open', $event)"
  >
    <div
      class="snapshot-fullsize__box"
      :class="{ 'snapshot-fullsize__box--alone': !props.snapshot.isProcessed }"
    >
      <div class="snapshot-fullsize__photo">
        <SnapshotImageOverlay
          :snapshot="props.snapshot"
          :detections="props.filteredDetections"
          :hovered-technique-id="props.hoveredTechniqueId"
          :hidden-technique-ids="props.hiddenTechniqueIds"
          :img-width="props.snapshot.width"
          :allow-full-size-mode="false"
        />
        <v-btn
          v-if="!props.snapshot.isProcessed"
          icon="mdi-close"
          size="x-small"
          variant="flat"
          class="snapshot-fullsize__close-float"
          @click="handleClose"
        />
      </div>

      <div v-if="props.snapshot.isProcessed" class="snapshot-fullsize__panel">
        <div class="snapshot-fullsize__panel-header">
          <span class="text-truncate" :title="props.snapshot.name">
            {{ props.snapshot.name }}
          </span>
          <v-spacer />
          <v-btn
            icon="mdi-close"
            size="small"
            variant="text"
            @click="handleClose"
          />
        </div>

        <SnapshotStats
          :grouped="props.grouped"
          :filtered-count="props.filteredDetections.length"
          :threshold="props.threshold"
          :hovered-technique-id="props.hoveredTechniqueId"
          :hidden-technique-ids="props.hiddenTechniqueIds"
          @hover="emit('hover', $event)"
          @toggle-hidden="emit('toggle-hidden', $event)"
        />

        <template v-if="props.open">
          <SnapshotThresholdSlider
            :model-value="props.threshold"
            class="snapshot-fullsize__threshold"
            @update:model-value="emit('update:threshold', $event)"
          />
        </template>
      </div>
    </div>
  </v-dialog>
</template>

<style scoped>
  .snapshot-fullsize__box {
    display: inline-flex;
    align-items: stretch;
    gap: 0;
    max-width: 95vw;
    max-height: 95vh;
    position: relative;
  }

  .snapshot-fullsize__photo {
    position: relative;
    min-width: 0;
    overflow: auto;
    max-width: calc(95vw - 320px);
    max-height: 95vh;
  }

  .snapshot-fullsize__box--alone .snapshot-fullsize__photo {
    max-width: 95vw;
  }

  .snapshot-fullsize__photo :deep(.snapshot-image-wrapper) {
    border-radius: 12px 0 0 12px;
  }

  .snapshot-fullsize__box--alone
    .snapshot-fullsize__photo
    :deep(.snapshot-image-wrapper) {
    border-radius: 12px;
  }

  .snapshot-fullsize__panel {
    width: 320px;
    flex-shrink: 0;
    background: rgb(var(--v-theme-surface));
    border-radius: 0 12px 12px 0;
    padding: 16px;
    overflow-y: auto;
    max-height: 95vh;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .snapshot-fullsize__panel-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    font-size: 14px;
  }

  .snapshot-fullsize__threshold {
    padding: 16px 20px 20px;
    border: 1px solid #e0e7f0;
    border-radius: 12px;
    background: #ffffff;
  }

  .snapshot-fullsize__close-float {
    position: absolute;
    bottom: 8px;
    right: 8px;
    z-index: 2;
    background: rgba(0, 0, 0, 0.45) !important;
    color: #fff !important;
    border-radius: 4px;
  }

  .snapshot-fullsize__close-float:hover {
    background: rgba(0, 0, 0, 0.65) !important;
  }

  .snapshot-fullsize__close-float :deep(.v-icon) {
    color: #fff;
  }

  @media (max-width: 960px) {
    .snapshot-fullsize__box {
      display: flex;
      flex-direction: column;
      max-width: 95vw;
    }

    .snapshot-fullsize__photo {
      max-width: 95vw;
      max-height: 60vh;
    }

    .snapshot-fullsize__photo :deep(.snapshot-image-wrapper) {
      border-radius: 12px 12px 0 0;
    }

    .snapshot-fullsize__box--alone
      .snapshot-fullsize__photo
      :deep(.snapshot-image-wrapper) {
      border-radius: 12px;
    }

    .snapshot-fullsize__panel {
      width: 100%;
      border-radius: 0 0 12px 12px;
      max-height: 40vh;
    }
  }
</style>

<style>
  .snapshot-fullsize-dialog {
    background: transparent !important;
    box-shadow: none !important;
    padding: 0;
  }
</style>
