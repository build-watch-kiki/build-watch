<script setup lang="ts">
  import { computed, ref, watch } from 'vue'
  import type { Snapshot } from '@/types/snapshots.ts'
  import { getDetectionStats } from '@/utils/snapshots.ts'
  import SnapshotImageOverlay from './SnapshotImageOverlay.vue'
  import SnapshotStats from './SnapshotStats.vue'
  import SnapshotThresholdSlider from './SnapshotThresholdSlider.vue'
  import SnapshotFullsizeDialog from './SnapshotFullsizeDialog.vue'

  defineOptions({ name: 'SnapshotExpand' })

  interface Props {
    snapshot: Snapshot
    allowFullSizeMode?: boolean
  }

  const props = withDefaults(defineProps<Props>(), {
    allowFullSizeMode: true
  })

  const threshold = ref(75)
  const selectedTechniqueId = ref<number | null>(null)
  const pointerTechniqueId = ref<number | null>(null)
  const focusTechniqueId = ref<number | null>(null)
  const hiddenTechniqueIds = ref<Set<number>>(new Set())
  const isFullsizeOpen = ref(false)

  const activeTechniqueId = computed(
    () =>
      pointerTechniqueId.value ??
      focusTechniqueId.value ??
      selectedTechniqueId.value
  )

  const filteredDetections = computed(() =>
    props.snapshot.detections.filter(
      (d) => d.confidence.detection * 100 >= threshold.value
    )
  )

  const groupedStats = computed(() =>
    getDetectionStats(filteredDetections.value)
  )

  function toggleHidden(techniqueId: number) {
    const next = new Set(hiddenTechniqueIds.value)
    if (next.has(techniqueId)) {
      next.delete(techniqueId)
    } else {
      next.add(techniqueId)
    }
    hiddenTechniqueIds.value = next
  }

  function resetInteraction() {
    selectedTechniqueId.value = null
    pointerTechniqueId.value = null
    focusTechniqueId.value = null
    hiddenTechniqueIds.value = new Set()
  }

  watch(
    () => [
      props.snapshot.projectId,
      props.snapshot.id,
      props.snapshot.capturedAt,
      props.snapshot.url
    ],
    resetInteraction
  )
</script>

<template>
  <div class="snapshot-expand">
    <div class="snapshot-evidence">
      <SnapshotImageOverlay
        :snapshot="snapshot"
        :detections="filteredDetections"
        :hovered-technique-id="activeTechniqueId"
        :hidden-technique-ids="hiddenTechniqueIds"
        :allow-full-size-mode="props.allowFullSizeMode"
        @open-fullsize="isFullsizeOpen = true"
      />
      <div class="snapshot-evidence-caption">
        <span
          ><v-icon size="14">mdi-image-outline</v-icon>
          {{
            snapshot.demo
              ? 'Демонстрационная иллюстрация'
              : 'Фотография площадки'
          }}</span
        ><span>Цвет рамки соответствует технике в легенде</span>
      </div>
    </div>
    <div class="snapshot-side">
      <v-alert
        v-if="!snapshot.isProcessed"
        type="info"
        variant="tonal"
        title="Фотография обрабатывается"
      >
        Результаты распознавания появятся после завершения обработки. Журнал
        обновляется автоматически.
      </v-alert>
      <template v-else>
        <SnapshotStats
          :grouped="groupedStats"
          :filtered-count="filteredDetections.length"
          :threshold="threshold"
          :hovered-technique-id="activeTechniqueId"
          :selected-technique-id="selectedTechniqueId"
          :hidden-technique-ids="hiddenTechniqueIds"
          @hover="pointerTechniqueId = $event"
          @focus="focusTechniqueId = $event"
          @select="selectedTechniqueId = $event"
          @toggle-hidden="toggleHidden"
        />
        <SnapshotThresholdSlider
          v-model="threshold"
          class="snapshot-threshold"
        />
      </template>
    </div>

    <SnapshotFullsizeDialog
      v-if="props.allowFullSizeMode"
      :open="isFullsizeOpen"
      :snapshot="props.snapshot"
      :filtered-detections="filteredDetections"
      :grouped="groupedStats"
      :threshold="threshold"
      :hovered-technique-id="activeTechniqueId"
      :hidden-technique-ids="hiddenTechniqueIds"
      @update:open="isFullsizeOpen = $event"
      @hover="pointerTechniqueId = $event"
      @toggle-hidden="toggleHidden"
      @update:threshold="threshold = $event"
    />
  </div>
</template>

<style scoped>
  .snapshot-expand {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(220px, 280px);
    align-items: start;
    gap: 20px;
    width: 100%;
  }
  .snapshot-evidence {
    min-width: 0;
  }
  .snapshot-evidence-caption {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 8px;
    margin-top: 10px;
    font-size: 11px;
    color: #5f7188;
    line-height: 1.5;
  }
  .snapshot-evidence-caption > span:first-child {
    display: flex;
    align-items: center;
    gap: 5px;
  }
  .snapshot-side {
    display: grid;
    gap: 12px;
    min-width: 0;
  }
  .snapshot-threshold {
    padding: 16px 20px 20px;
    border: 1px solid #e0e7f0;
    border-radius: 12px;
    background: #ffffff;
  }
  @media (max-width: 1100px) {
    .snapshot-expand {
      grid-template-columns: minmax(0, 1fr);
    }
  }
</style>
