<script setup lang="ts">
  import { computed, ref, watch } from 'vue'
  import DataFormDialog from '@/components/DataFormDialog.vue'
  import { displayDate } from '@/utils/datetime'
  import type { DateString } from '@/types/api.ts'
  import {
    MAX_UPLOAD_BATCH,
    type PhotoUploadEntry,
    type PhotoUploadItem
  } from '@/services/photos.ts'
  import {
    ACCEPTED_PHOTO_ACCEPT,
    ACCEPTED_PHOTO_TYPES,
    validatePhoto
  } from '@/utils/photos.ts'

  interface Props {
    open: boolean
    loading: boolean
    error: string | null
    items: PhotoUploadItem[]
    minDate?: DateString | null
    maxDate?: DateString | null
  }

  const props = withDefaults(defineProps<Props>(), {
    minDate: null,
    maxDate: null
  })

  const emit = defineEmits<{
    ok: [entries: PhotoUploadEntry[]]
    cancel: []
  }>()

  const files = ref<File[]>([])
  const dates = ref<Record<string, string>>({})
  const isDragging = ref(false)
  const fileInputRef = ref<HTMLInputElement | null>(null)

  const dataObject = computed(() => ({
    files: files.value
  }))

  const hasErrors = computed(() =>
    props.items.some((item) => item.status === 'error')
  )
  const acceptedCount = computed(
    () => props.items.filter((item) => item.status === 'accepted').length
  )

  const dropError = computed<string | null>(() => {
    if (!files.value.length) return 'Выберите хотя бы один файл'
    if (files.value.length > MAX_UPLOAD_BATCH) {
      return `За один раз можно загрузить не более ${MAX_UPLOAD_BATCH} файлов`
    }
    const invalid = files.value.find((file) => validatePhoto(file))
    if (invalid) {
      return `${invalid.name}: ${validatePhoto(invalid)}`
    }
    const outOfRange = files.value.find((file) => dateRangeError(getDate(file)))
    if (outOfRange) {
      return `${outOfRange.name}: ${dateRangeError(getDate(outOfRange))}`
    }
    return null
  })

  function dateRangeError(date: string): string | null {
    if (!date) return null
    if (props.minDate && date < props.minDate) return rangeMessage()
    if (props.maxDate && date > props.maxDate) return rangeMessage()
    return null
  }

  function rangeMessage(): string {
    const from = props.minDate ? displayDate(props.minDate) : '…'
    const to = props.maxDate ? displayDate(props.maxDate) : '…'
    return `Дата снимка должна быть с ${from} по ${to}`
  }

  function dateRules(value: string | null): true | string {
    if (!value) return true
    return dateRangeError(value) ?? true
  }

  function fileKey(file: File): string {
    return `${file.name}:${file.size}:${file.lastModified}`
  }

  function addFiles(list: FileList | File[] | null | undefined) {
    if (!list || props.loading) return
    const existing = new Set(files.value.map(fileKey))
    const next = [...files.value]
    for (const file of Array.from(list)) {
      if (!(ACCEPTED_PHOTO_TYPES as readonly string[]).includes(file.type))
        continue
      if (existing.has(fileKey(file))) continue
      if (next.length >= MAX_UPLOAD_BATCH) break
      existing.add(fileKey(file))
      next.push(file)
    }
    files.value = next
  }

  function removeFile(index: number) {
    const removed = files.value[index]
    files.value = files.value.filter((_, i) => i !== index)
    if (removed) {
      const next = { ...dates.value }
      delete next[fileKey(removed)]
      dates.value = next
    }
  }

  function getDate(file: File): string {
    return dates.value[fileKey(file)] ?? ''
  }

  function setDate(file: File, value: string | null) {
    const next = { ...dates.value }
    if (value) {
      next[fileKey(file)] = value
    } else {
      delete next[fileKey(file)]
    }
    dates.value = next
  }

  function openPicker() {
    if (props.loading) return
    fileInputRef.value?.click()
  }

  function handleInputChange(event: Event) {
    const input = event.target as HTMLInputElement
    addFiles(input.files)
    input.value = ''
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault()
    isDragging.value = false
    addFiles(event.dataTransfer?.files)
  }

  function resetForm() {
    files.value = []
    dates.value = {}
    isDragging.value = false
    if (fileInputRef.value) fileInputRef.value.value = ''
  }

  watch(
    () => props.open,
    (open) => {
      if (open) resetForm()
    }
  )

  async function handleOk() {
    if (dropError.value || !files.value.length) return
    emit(
      'ok',
      files.value.map((file) => ({
        file,
        capturedAt: dates.value[fileKey(file)] || null
      }))
    )
  }

  function handleCancel() {
    emit('cancel')
  }
</script>

<template>
  <DataFormDialog
    :open="props.open"
    :loading="props.loading"
    :error="props.error"
    :data-object="dataObject as unknown as Record<string, unknown>"
    :labels="{
      title: 'Загрузить снимки',
      ok: hasErrors ? 'Повторить попытку' : 'Загрузить'
    }"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <form @submit.prevent>
      <div
        class="upload-dropzone"
        :class="{
          'upload-dropzone--dragging': isDragging,
          'upload-dropzone--error': !!dropError && files.length > 0,
          'upload-dropzone--disabled': props.loading
        }"
        role="button"
        tabindex="0"
        aria-label="Выбрать фотографии площадки"
        @click="openPicker"
        @keydown.enter.prevent="openPicker"
        @keydown.space.prevent="openPicker"
        @dragenter.prevent="isDragging = true"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop="handleDrop"
      >
        <v-icon size="36" color="primary">mdi-cloud-upload-outline</v-icon>
        <div class="upload-dropzone__title">
          Перетащите файлы сюда или нажмите для выбора
        </div>
        <div class="upload-dropzone__subtitle">Фотографии площадки</div>
        <input
          ref="fileInputRef"
          type="file"
          multiple
          :accept="ACCEPTED_PHOTO_ACCEPT"
          class="upload-dropzone__input"
          tabindex="-1"
          :disabled="props.loading"
          @change="handleInputChange"
        />
      </div>
      <div v-if="files.length" class="upload-files">
        <div
          v-for="(file, idx) in files"
          :key="`${file.name}:${file.size}:${file.lastModified}`"
          class="upload-file-row"
        >
          <span class="upload-file-row__name" :title="file.name">{{
            file.name
          }}</span>
          <v-text-field
            :model-value="getDate(file)"
            label="Дата снимка"
            type="date"
            clearable
            :min="props.minDate ?? undefined"
            :max="props.maxDate ?? undefined"
            :rules="[dateRules]"
            hide-details="auto"
            density="compact"
            variant="outlined"
            class="upload-file-row__date"
            :disabled="props.loading"
            @update:model-value="setDate(file, $event)"
          />
          <v-btn
            icon="mdi-close"
            variant="text"
            density="comfortable"
            size="small"
            :disabled="props.loading"
            :aria-label="`Убрать ${file.name}`"
            @click="removeFile(idx)"
          />
        </div>
      </div>
      <p v-if="dropError && files.length" class="upload-error text-error">
        {{ dropError }}
      </p>
      <p class="upload-note">
        До {{ MAX_UPLOAD_BATCH }} файлов JPEG или PNG, не более 20 МБ каждый.
        Одновременно можно загрузить до трёх файлов. Дату снимка можно указать
        для каждого файла отдельно, это необязательно.
      </p>
      <div v-if="props.items.length" class="upload-progress" aria-live="polite">
        <div class="upload-progress__summary">
          Принято в обработку: {{ acceptedCount }} / {{ props.items.length }}
        </div>
        <ul>
          <li v-for="item in props.items" :key="item.key">
            <v-icon
              size="17"
              :class="{ 'mdi-spin': item.status === 'uploading' }"
              :color="
                item.status === 'accepted'
                  ? 'success'
                  : item.status === 'error'
                    ? 'error'
                    : 'primary'
              "
            >
              {{
                item.status === 'accepted'
                  ? 'mdi-check-circle'
                  : item.status === 'error'
                    ? 'mdi-alert-circle'
                    : item.status === 'uploading'
                      ? 'mdi-loading'
                      : 'mdi-clock-outline'
              }}
            </v-icon>
            <span>{{ item.file.name }}</span>
            <small v-if="item.status === 'error'">{{ item.error }}</small>
            <small v-else-if="item.status === 'accepted'">Принят</small>
            <small v-else-if="item.status === 'uploading'">Загрузка…</small>
            <small v-else>В очереди</small>
          </li>
        </ul>
      </div>
    </form>
  </DataFormDialog>
</template>

<style scoped>
  .upload-dropzone {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 28px 16px;
    border: 2px dashed #b6c4d6;
    border-radius: 12px;
    background: #f8fafc;
    cursor: pointer;
    transition:
      border-color 0.15s,
      background 0.15s;
  }

  .upload-dropzone:hover {
    border-color: rgb(var(--v-theme-primary));
    background: rgba(var(--v-theme-primary), 0.04);
  }

  .upload-dropzone:focus-visible {
    outline: 2px solid rgb(var(--v-theme-primary));
    outline-offset: 2px;
  }

  .upload-dropzone--dragging {
    border-color: rgb(var(--v-theme-primary));
    background: rgba(var(--v-theme-primary), 0.08);
  }

  .upload-dropzone--error {
    border-color: rgb(var(--v-theme-error));
  }

  .upload-dropzone--disabled {
    opacity: 0.6;
    cursor: default;
    pointer-events: none;
  }

  .upload-dropzone__title {
    font-size: 14px;
    font-weight: 600;
    text-align: center;
  }

  .upload-dropzone__subtitle {
    font-size: 12px;
    color: #65758b;
  }

  .upload-dropzone__input {
    position: absolute;
    width: 1px;
    height: 1px;
    opacity: 0;
    pointer-events: none;
  }

  .upload-files {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 12px;
  }

  .upload-file-row {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }

  .upload-file-row__name {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 13px;
  }

  .upload-file-row__date {
    width: 170px;
    flex-shrink: 0;
  }

  .upload-error {
    margin-top: 8px;
    font-size: 12px;
  }

  .upload-note {
    margin-top: 8px;
    color: #65758b;
    font-size: 12px;
    line-height: 1.5;
  }
  .upload-progress {
    display: grid;
    gap: 10px;
    margin-top: 16px;
  }
  .upload-progress__summary {
    font-size: 13px;
    font-weight: 650;
  }
  .upload-progress ul {
    display: grid;
    gap: 7px;
    max-height: 240px;
    overflow-y: auto;
    padding: 0;
    list-style: none;
  }
  .upload-progress li {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
    gap: 8px;
    font-size: 12px;
  }
  .upload-progress li > span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .upload-progress li > small {
    max-width: 180px;
    overflow: hidden;
    color: #65758b;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
