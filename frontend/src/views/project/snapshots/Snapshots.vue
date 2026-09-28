<script setup lang="ts">
  import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import type { DataTableHeader } from 'vuetify/framework'

  import { useProjectSnapshotsStore } from '@/store/snapshots.ts'
  import type { Snapshot } from '@/types/snapshots.ts'
  import { displayDate } from '@/utils/datetime'
  import { getApiErrorDetail } from '@/utils/errors'
  import {
    cutFileName,
    downloadSnapshotFile,
    getDetectionStats,
    getDetectionsAvg,
    getObjectWord
  } from '@/utils/snapshots'
  import { uploadPhotoBatch, type PhotoUploadItem } from '@/services/photos.ts'

  import UploadSnapshotDialog from './components/UploadSnapshotDialog.vue'
  import LoadingPlaceholder from '@/components/LoadingPlaceholder.vue'
  import SnapshotExpand from '@/views/project/snapshots/components/SnapshotExpand.vue'

  const route = useRoute()
  const router = useRouter()
  const snapshotsStore = useProjectSnapshotsStore()

  const projectId = computed(() => Number(route.params.projectId))

  const list = computed(() => snapshotsStore.getList)
  const loadingState = computed(() => snapshotsStore.getLoadingState)
  const pagination = computed(() => snapshotsStore.getPagination)
  const detail = computed(() => snapshotsStore.getDetail)
  const detectionCount = computed(() =>
    list.value.reduce((total, item) => total + rawOf(item).detections.length, 0)
  )

  const page = ref(1)
  const itemsPerPage = ref(10)
  const statusFilter = ref<boolean | null>(null)
  const expanded = ref<string[]>([])
  const listError = ref<string | null>(null)

  const statusOptions = [
    { title: 'Все', value: null },
    { title: 'Обработан', value: true },
    { title: 'Не завершено', value: false }
  ]

  const headers: DataTableHeader[] = [
    {
      title: 'Дата и время',
      key: 'capturedAt',
      sortable: false,
      align: 'center',
      width: '15%'
    },
    {
      title: 'Статус',
      key: 'isProcessed',
      sortable: false,
      align: 'center',
      width: '15%'
    },
    {
      title: 'Распознанная техника',
      key: 'detectionsCount',
      sortable: false,
      align: 'start',
      width: '30%'
    },
    {
      title: 'Модель',
      key: 'model',
      sortable: false,
      align: 'center',
      width: '15%'
    },
    {
      title: 'Файл',
      key: 'file',
      sortable: false,
      align: 'start',
      width: '20%'
    },
    {
      title: '',
      key: 'data-table-expand',
      sortable: false,
      align: 'center',
      width: '5%'
    }
  ]

  async function loadPage(silent = false) {
    if (!silent) listError.value = null
    try {
      await snapshotsStore.loadPaginatedList(
        { projectId: projectId.value },
        {
          page: page.value,
          pageSize: itemsPerPage.value,
          ...(statusFilter.value != null
            ? { isProcessed: statusFilter.value }
            : {})
        },
        false,
        silent
      )
    } catch (error: unknown) {
      if (!silent) {
        listError.value = getApiErrorDetail(
          error,
          'Не удалось загрузить снимки'
        )
      }
    }
  }

  function handleUpdateOptions(options: {
    page: number
    itemsPerPage: number
  }) {
    const changed =
      options.page !== page.value || options.itemsPerPage !== itemsPerPage.value
    page.value = options.page
    itemsPerPage.value = options.itemsPerPage
    if (changed) void loadPage()
  }

  watch(statusFilter, () => {
    expanded.value = []
    page.value = 1
    void loadPage()
  })

  watch(projectId, () => {
    page.value = 1
    expanded.value = []
    void loadPage()
  })

  function rawOf(item: unknown): Snapshot {
    return ((item as { raw?: Snapshot }).raw ?? item) as Snapshot
  }

  function formatRowDate(item: unknown): string {
    const snapshot = rawOf(item)
    return displayDate(snapshot.capturedAt ?? snapshot.createdAt, true)
  }

  function formatModel(item: unknown): string {
    const model = rawOf(item).model
    if (!model) return '—'
    return `${model.name} ${model.version}`
  }

  function processingLabel(snapshot: Snapshot): string {
    return {
      pending: 'В обработке',
      succeeded: 'Обработан',
      failed: 'Ошибка обработки'
    }[snapshot.processingStatus]
  }

  function processingIcon(snapshot: Snapshot): string {
    return {
      pending: 'mdi-progress-clock',
      succeeded: 'mdi-check-circle',
      failed: 'mdi-alert-circle'
    }[snapshot.processingStatus]
  }

  function processingColor(snapshot: Snapshot): string {
    return {
      pending: 'warning',
      succeeded: 'success',
      failed: 'error'
    }[snapshot.processingStatus]
  }

  function detectionStats(item: unknown) {
    return getDetectionStats(rawOf(item).detections)
  }

  function handleDownload(item: unknown) {
    void downloadSnapshotFile(rawOf(item))
  }

  const showUploadDialog = ref(false)
  const uploadLoading = ref(false)
  const uploadError = ref<string | null>(null)
  const uploadItems = ref<PhotoUploadItem[]>([])

  function openUploadDialog() {
    uploadError.value = null
    uploadItems.value = []
    showUploadDialog.value = true
  }

  async function handleUploadOk(files: File[]) {
    uploadLoading.value = true
    uploadError.value = null
    const accepted = uploadItems.value.filter(
      (item) => item.status === 'accepted'
    )
    const retryFiles = uploadItems.value.some((item) => item.status === 'error')
      ? uploadItems.value
          .filter((item) => item.status === 'error')
          .map((item) => item.file)
      : files
    const result = await uploadPhotoBatch(
      projectId.value,
      retryFiles,
      (items) => {
        uploadItems.value = [...accepted, ...items]
      }
    )
    uploadItems.value = [...accepted, ...result]
    uploadLoading.value = false

    const failures = uploadItems.value.filter((item) => item.status === 'error')
    const filterChanged = statusFilter.value !== null
    statusFilter.value = null
    page.value = 1
    expanded.value = []
    try {
      if (!filterChanged) await loadPage()
    } catch {
      // The visible list already contains a user-facing error.
    }
    if (failures.length) {
      uploadError.value = `Не удалось загрузить ${failures.length} из ${uploadItems.value.length} файлов`
    } else {
      showUploadDialog.value = false
      clearUploadQuery()
    }
  }

  function handleUploadCancel() {
    showUploadDialog.value = false
    uploadError.value = null
    clearUploadQuery()
  }

  const requestedUpload = computed(() => {
    const raw = Array.isArray(route.query.upload)
      ? route.query.upload[0]
      : route.query.upload
    return raw === '1'
  })

  function clearUploadQuery() {
    if (route.query.upload == null) return
    const query = { ...route.query }
    delete query.upload
    void router.replace({ query })
  }

  watch(
    requestedUpload,
    (requested) => {
      if (requested && !showUploadDialog.value) openUploadDialog()
    },
    { immediate: true }
  )

  const hasPendingPhotos = computed(() =>
    list.value.some((item) => rawOf(item).processingStatus === 'pending')
  )
  let pollTimer: ReturnType<typeof setTimeout> | null = null
  let pollInFlight = false

  function stopPolling() {
    if (pollTimer !== null) clearTimeout(pollTimer)
    pollTimer = null
  }

  function schedulePolling() {
    stopPolling()
    if (!hasPendingPhotos.value || document.visibilityState !== 'visible')
      return
    pollTimer = setTimeout(() => void pollPage(), 3000)
  }

  async function pollPage() {
    if (pollInFlight || loadingState.value.list) {
      schedulePolling()
      return
    }
    pollInFlight = true
    try {
      await loadPage(true)
    } catch {
      // A transient background error must not replace the visible journal.
    } finally {
      pollInFlight = false
      schedulePolling()
    }
  }

  function handleVisibilityChange() {
    if (document.visibilityState === 'visible' && hasPendingPhotos.value) {
      void pollPage()
    } else {
      stopPolling()
    }
  }

  watch(hasPendingPhotos, schedulePolling)

  const requestedPhotoId = computed(() => {
    const raw = Array.isArray(route.query.photoId)
      ? route.query.photoId[0]
      : route.query.photoId
    return raw && /^\d+$/.test(raw) ? Number(raw) : null
  })
  const detailError = ref<string | null>(null)

  watch(
    [projectId, requestedPhotoId],
    async ([pid, photoId]) => {
      detailError.value = null
      if (!photoId) {
        snapshotsStore.clearDetail()
        return
      }
      try {
        await snapshotsStore.loadDetail({ projectId: pid, photoId })
      } catch (error: unknown) {
        detailError.value = getApiErrorDetail(
          error,
          'Не удалось открыть фотографию'
        )
      }
    },
    { immediate: true }
  )

  function closePhotoDetail() {
    const query = { ...route.query }
    delete query.photoId
    void router.replace({ query })
  }

  onMounted(() => {
    document.addEventListener('visibilitychange', handleVisibilityChange)
    void loadPage()
  })

  onBeforeUnmount(() => {
    stopPolling()
    document.removeEventListener('visibilitychange', handleVisibilityChange)
    snapshotsStore.clearDetail()
  })
</script>

<template>
  <div class="snapshot-journal">
    <Teleport defer to="#page-header-actions">
      <v-btn color="info" prepend-icon="mdi-upload" @click="openUploadDialog">
        Загрузить
      </v-btn>
    </Teleport>
    <section class="journal-intro">
      <div>
        <h2>Фотографии площадки</h2>
        <p class="bw-muted">
          Загрузите свои снимки и откройте фотографию, чтобы посмотреть
          найденную технику. Статус обработки обновляется автоматически.
        </p>
      </div>
    </section>
    <v-alert
      v-if="listError"
      type="error"
      variant="tonal"
      title="Не удалось загрузить снимки"
    >
      {{ listError }}
      <div class="mt-3">
        <v-btn size="small" variant="outlined" @click="loadPage()"
          >Повторить</v-btn
        >
      </div>
    </v-alert>
    <div class="journal-summary">
      <div>
        <v-icon size="22">mdi-camera-outline</v-icon
        ><span
          ><strong>{{ pagination?.total ?? 0 }}</strong> фотографий в
          журнале</span
        >
      </div>
      <div>
        <v-icon size="22">mdi-vector-square</v-icon
        ><span
          ><strong>{{ detectionCount }}</strong> объектов на показанных
          фотографиях</span
        >
      </div>
      <div>
        <v-icon size="22">mdi-palette-outline</v-icon
        ><span>Цвет помогает различать технику</span>
      </div>
    </div>
    <section class="bw-panel journal-card">
      <div class="journal-table-heading">
        <h3>Снимки площадки</h3>
        <span class="bw-muted">Сначала последние</span>
      </div>
      <v-data-table-server
        v-model:expanded="expanded"
        v-model:items-per-page="itemsPerPage"
        style="font-size: 18px"
        :page="page"
        :items="list"
        :headers="headers"
        :loading="loadingState.list"
        :items-length="pagination?.total ?? 0"
        item-value="id"
        show-expand
        expand-strategy="single"
        @update:options="handleUpdateOptions"
      >
        <template #loading>
          <v-container
            fluid
            class="flex-grow-1 d-flex flex-column"
            min-height="400"
          >
            <loading-placeholder size="large" />
          </v-container>
        </template>
        <template #footer.prepend>
          <v-row no-gutters class="align-center">
            <span class="ml-3">Фильтр:</span>
            <v-select
              v-model="statusFilter"
              :items="statusOptions"
              max-width="200"
              label="Статус"
              density="compact"
              variant="outlined"
              hide-details
              class="ml-3 snapshot-status-filter"
            />
          </v-row>
        </template>
        <template #item.capturedAt="{ item }">
          {{ formatRowDate(item) }}
        </template>

        <template #item.isProcessed="{ item }">
          <span class="d-inline-flex align-center">
            <v-icon
              :icon="processingIcon(rawOf(item))"
              :color="processingColor(rawOf(item))"
              size="18"
              class="mr-1"
            />
            {{ processingLabel(rawOf(item)) }}
          </span>
        </template>

        <template #item.detectionsCount="{ item }">
          <div
            v-if="rawOf(item).processingStatus === 'succeeded'"
            class="technique-summary"
          >
            <div class="technique-summary__meta">
              {{ rawOf(item).detections.length }}
              {{ getObjectWord(rawOf(item).detections.length) }} ·
              {{ getDetectionsAvg(rawOf(item).detections) }}
            </div>
            <div v-if="detectionStats(item).length" class="technique-chips">
              <span
                v-for="stat in detectionStats(item).slice(0, 3)"
                :key="stat.objectClass"
                class="technique-chip"
                :title="`${stat.objectClass}: ${stat.count}`"
              >
                {{ stat.objectClass }} ×{{ stat.count }}
              </span>
              <span
                v-if="detectionStats(item).length > 3"
                class="technique-chip technique-chip--more"
              >
                +{{ detectionStats(item).length - 3 }}
              </span>
            </div>
            <span v-else class="technique-summary__empty">Не распознана</span>
          </div>
          <span v-else class="technique-summary__empty">—</span>
        </template>

        <template #item.model="{ item }">
          {{ formatModel(item) }}
        </template>

        <template #item.file="{ item }">
          <a
            href="#"
            class="snapshot-file-link text-info"
            :title="rawOf(item).name"
            @click.prevent="handleDownload(item)"
          >
            {{ cutFileName(rawOf(item).name, 30) }}
            <v-icon size="24" class="ml-1 text-decoration-none"
              >mdi-download</v-icon
            >
          </a>
        </template>

        <template #expanded-row="{ columns, item }">
          <tr>
            <td :colspan="columns.length" class="pa-4">
              <SnapshotExpand :snapshot="rawOf(item)" />
            </td>
          </tr>
        </template>
        <template #no-data>
          <div class="journal-empty">
            <v-icon icon="mdi-camera-plus-outline" size="40" color="primary" />
            <h3>Добавьте первые фотографии площадки</h3>
            <p>
              Выберите JPEG или PNG, чтобы проверить работу распознавания на
              своих снимках.
            </p>
            <v-btn color="primary" variant="flat" @click="openUploadDialog"
              >Загрузить фотографии</v-btn
            >
          </div>
        </template>
      </v-data-table-server>
    </section>

    <UploadSnapshotDialog
      :open="showUploadDialog"
      :loading="uploadLoading"
      :error="uploadError"
      :items="uploadItems"
      @ok="handleUploadOk"
      @cancel="handleUploadCancel"
    />

    <v-dialog
      :model-value="requestedPhotoId !== null"
      max-width="1400"
      scrollable
      @update:model-value="!$event && closePhotoDetail()"
    >
      <v-card class="photo-detail-dialog">
        <v-card-title class="photo-detail-dialog__header">
          <span>Фотография из журнала</span>
          <v-btn
            icon="mdi-close"
            variant="text"
            aria-label="Закрыть фотографию"
            @click="closePhotoDetail"
          />
        </v-card-title>
        <v-card-text>
          <loading-placeholder v-if="loadingState.detail" size="large" />
          <v-alert
            v-else-if="detailError"
            type="error"
            variant="tonal"
            title="Не удалось открыть фотографию"
          >
            {{ detailError }}
          </v-alert>
          <SnapshotExpand v-else-if="detail" :snapshot="detail" />
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
  .snapshot-journal {
    display: grid;
    gap: 24px;
  }
  .journal-intro {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 20px;
  }
  .journal-intro h2 {
    font-size: 24px;
    letter-spacing: -0.5px;
    margin: 6px 0 8px;
  }
  .journal-intro p {
    font-size: 16px;
    max-width: 620px;
  }
  .journal-summary {
    display: flex;
    flex-wrap: wrap;
    gap: 16px 32px;
    padding: 19px 24px;
    background: #eaf0f8;
    border: 1px solid #dfe7f2;
    border-radius: 12px;
    color: #41556e;
    font-size: 14px;
  }
  .journal-summary > div {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .journal-summary strong {
    color: #182536;
  }
  .journal-card {
    overflow: hidden;
  }
  .technique-summary {
    display: grid;
    gap: 5px;
    padding: 7px 0;
  }
  .technique-summary__meta,
  .technique-summary__empty {
    color: #65758b;
    font-size: 11px;
  }
  .technique-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  .technique-chip {
    display: inline-flex;
    max-width: 150px;
    padding: 3px 7px;
    overflow: hidden;
    border: 1px solid #dbe5f1;
    border-radius: 999px;
    background: #f1f5fa;
    color: #334a67;
    font-size: 10px;
    font-weight: 650;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .technique-chip--more {
    background: #e6eef9;
    color: #1d4ed8;
  }
  .photo-detail-dialog {
    max-height: calc(100dvh - 48px);
  }
  .photo-detail-dialog__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .journal-table-heading {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid #e8edf3;
  }
  .journal-table-heading h3 {
    font-size: 16px;
  }
  .journal-table-heading span {
    font-size: 13px;
  }
  .journal-empty {
    padding: 40px 24px;
    text-align: center;
  }
  .journal-empty h3 {
    margin: 16px 0 12px;
    font-size: 22px;
  }
  .journal-empty p {
    margin-bottom: 24px;
    color: #5b6b80;
    font-size: 16px;
  }
  .snapshot-status-filter {
    max-width: 320px;
  }

  .snapshot-file-link {
    text-decoration: underline;
    text-underline-offset: 2px;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    word-break: break-all;
  }

  .snapshot-file-link .v-icon {
    display: inline-block;
    text-decoration: none;
  }
  @media (max-width: 767px) {
    .journal-intro {
      flex-direction: column;
    }
    .journal-intro h2 {
      font-size: 22px;
    }
    .journal-summary {
      padding: 16px;
      gap: 14px;
      flex-direction: column;
    }
    .journal-table-heading {
      padding: 18px 16px;
    }
  }
</style>
