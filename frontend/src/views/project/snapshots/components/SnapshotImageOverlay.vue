<script setup lang="ts">
  import { computed, ref, watch } from 'vue'
  import type { Snapshot, SnapshotDetection } from '@/types/snapshots.ts'
  import {
    formatConfidence,
    getBoxStyle,
    getDetectionColor,
    getDetectionLabelColor
  } from '@/utils/snapshots.ts'

  defineOptions({ name: 'SnapshotImageOverlay' })

  interface Props {
    snapshot: Snapshot
    detections: SnapshotDetection[]
    hoveredTechniqueId?: number | null
    hiddenTechniqueIds?: Set<number>
    imgWidth?: number | string
    allowFullSizeMode?: boolean
  }

  const props = withDefaults(defineProps<Props>(), {
    hoveredTechniqueId: null,
    hiddenTechniqueIds: () => new Set<number>(),
    imgWidth: undefined,
    allowFullSizeMode: true
  })

  const emit = defineEmits<{
    'open-fullsize': []
  }>()

  const wrapStyle = computed<Record<string, string>>(() => {
    if (props.imgWidth == null || props.imgWidth === '') {
      return { width: '100%' }
    }
    return {
      width:
        typeof props.imgWidth === 'number'
          ? `${props.imgWidth}px`
          : props.imgWidth
    }
  })

  const naturalWidth = ref(0)
  const naturalHeight = ref(0)
  const imageError = ref(false)
  const imageKey = computed(
    () =>
      `${props.snapshot.projectId}:${props.snapshot.id}:${props.snapshot.capturedAt}:${props.snapshot.url}`
  )
  watch(
    imageKey,
    () => {
      naturalWidth.value = 0
      naturalHeight.value = 0
      imageError.value = false
    },
    { flush: 'sync' }
  )
  const boxes = computed(() =>
    props.detections
      .filter(
        (detection) => !props.hiddenTechniqueIds.has(detection.technique.id)
      )
      .map((detection) => {
        const color = getDetectionColor(detection)
        const techniqueId = detection.technique.id
        const { yCenterNorm, hNorm } = detection.bbox
        const inside =
          typeof yCenterNorm === 'number' &&
          typeof hNorm === 'number' &&
          yCenterNorm - hNorm / 2 < 0.06
        return {
          detection,
          techniqueId,
          inside,
          label: `${detection.technique.nameRu}: ${formatConfidence(detection.confidence.detection)}`,
          dimmed:
            props.hoveredTechniqueId !== null &&
            props.hoveredTechniqueId !== techniqueId,
          highlighted: props.hoveredTechniqueId === techniqueId,
          style: {
            ...getBoxStyle(detection, naturalWidth.value, naturalHeight.value),
            '--detection-color': color,
            '--detection-fill': `${color}20`,
            '--detection-highlight': `${color}55`,
            '--detection-label-color': getDetectionLabelColor(color)
          }
        }
      })
  )
  function onImageLoad(event: Event) {
    const img = event.target as HTMLImageElement
    naturalWidth.value = img.naturalWidth
    naturalHeight.value = img.naturalHeight
    imageError.value = false
  }
  function onImageError() {
    naturalWidth.value = 0
    naturalHeight.value = 0
    imageError.value = true
  }
</script>

<template>
  <div
    class="snapshot-image-wrapper"
    :class="{ 'snapshot-image-wrapper--error': imageError }"
    :style="wrapStyle"
  >
    <img
      v-if="!imageError"
      :key="imageKey"
      :src="snapshot.url"
      :alt="`Снимок площадки №${snapshot.id}; распознано объектов: ${detections.length}`"
      class="snapshot-image"
      @load="onImageLoad"
      @error="onImageError"
    />
    <div v-else class="snapshot-image-error" role="status">
      <v-icon size="32">mdi-image-broken-variant</v-icon
      ><strong>Не удалось загрузить снимок</strong
      ><span>Попробуйте открыть другое подтверждение.</span>
    </div>
    <template v-if="naturalWidth && naturalHeight && !imageError">
      <div
        v-for="(
          { detection, label, inside, dimmed, highlighted, style }, idx
        ) in boxes"
        :key="detection.objectId || idx"
        class="snapshot-box"
        :class="{ dimmed, highlighted }"
        :style="style"
        aria-hidden="true"
      >
        <span
          class="snapshot-box-label"
          :class="{ 'snapshot-box-label--inside': inside }"
          :title="label"
          >{{ label }}</span
        >
      </div>
    </template>
    <v-tooltip
      v-if="allowFullSizeMode && !imageError"
      text="Открыть в исходном размере"
      location="top"
    >
      <template #activator="{ props: tooltipProps }">
        <v-btn
          v-bind="tooltipProps"
          icon="mdi-fullscreen"
          size="x-small"
          variant="flat"
          class="snapshot-image-fullscreen"
          aria-label="Открыть в исходном размере"
          @click.stop="emit('open-fullsize')"
        />
      </template>
    </v-tooltip>
  </div>
</template>

<style scoped>
  .snapshot-image-wrapper {
    position: relative;
    width: 100%;
    line-height: 0;
    background: #e8edf3;
    border: 1px solid #dce5ee;
    border-radius: 12px;
    overflow: hidden;
  }
  .snapshot-image {
    width: 100%;
    height: auto;
    display: block;
  }
  .snapshot-box {
    position: absolute;
    border: 2px solid var(--detection-color);
    background: var(--detection-fill);
    border-radius: 4px;
    transition:
      opacity 180ms ease,
      box-shadow 180ms ease;
    pointer-events: auto;
  }
  .snapshot-box.dimmed {
    opacity: 0.18;
  }
  .snapshot-box.highlighted {
    opacity: 1;
    box-shadow: 0 0 0 3px var(--detection-highlight);
    z-index: 2;
  }
  .snapshot-box-label {
    position: absolute;
    top: -22px;
    left: -2px;
    color: var(--detection-label-color);
    background: var(--detection-color);
    font-size: clamp(8px, 1.1vw, 11px);
    font-weight: 600;
    line-height: 16px;
    padding: 2px 6px;
    border-radius: 4px;
    white-space: nowrap;
    overflow: visible;
    z-index: 3;
    opacity: 0;
    transition: opacity 120ms ease;
    pointer-events: none;
  }
  .snapshot-box-label--inside {
    top: 2px;
    left: 2px;
  }
  .snapshot-box:hover .snapshot-box-label {
    opacity: 1;
  }
  .snapshot-image-fullscreen {
    position: absolute;
    bottom: 8px;
    right: 8px;
    z-index: 2;
    background: rgba(0, 0, 0, 0.45) !important;
    color: #fff !important;
    border-radius: 4px;
    line-height: 1;
  }
  .snapshot-image-fullscreen:hover {
    background: rgba(0, 0, 0, 0.65) !important;
  }
  .snapshot-image-fullscreen :deep(.v-icon) {
    color: #fff;
  }
  .snapshot-image-wrapper--error {
    aspect-ratio: 8 / 5;
  }
  .snapshot-image-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    height: 100%;
    color: #5f7188;
    font-size: 13px;
    line-height: 1.5;
    padding: 24px;
    text-align: center;
  }
  @media (prefers-reduced-motion: reduce) {
    .snapshot-box {
      transition: none;
    }
  }
</style>
