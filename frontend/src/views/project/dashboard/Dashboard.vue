<script setup lang="ts">
  import { computed, nextTick, ref, watch } from 'vue'
  import { useRoute } from 'vue-router'
  import { useProjectsStore } from '@/store/projects'
  import { useProjectProgressStore } from '@/store/progress'
  import {
    adaptProgressDay,
    emptyDashboardDay,
    filterProgressDeviations,
    formatProgressDate
  } from '@/utils/progress'
  import { displayDate } from '@/utils/datetime'
  import { getObjectWord } from '@/utils/snapshots'
  import type { ProgressCategory, ProgressEquipment } from '@/types/progress'
  import SnapshotExpand from '@/views/project/snapshots/components/SnapshotExpand.vue'

  const route = useRoute()
  const projectsStore = useProjectsStore()
  const progressStore = useProjectProgressStore()
  const projectId = computed(() => Number(route.params.projectId))
  const project = computed(() => {
    const detail = projectsStore.getDetail
    return detail?.id === projectId.value ? detail : null
  })
  const days = computed(() =>
    [...progressStore.getHistory]
      .sort((left, right) => left.date.localeCompare(right.date))
      .map((summary) =>
        adaptProgressDay(summary, progressStore.getDetail, projectId.value)
      )
  )
  const loadError = ref<string | null>(null)
  const selectedDate = ref('')
  const selectedCategory = ref<ProgressCategory>('all')
  const expandedDeviationId = ref<string | null>(null)
  const selectedEvidenceId = ref<number | null>(null)
  const historyElement = ref<HTMLDivElement | null>(null)

  const currentDay = computed(
    () =>
      days.value.find((day) => day.date === selectedDate.value) ??
      days.value[days.value.length - 1] ??
      emptyDashboardDay(projectId.value)
  )
  const selectedDayIndex = computed(() =>
    days.value.findIndex((day) => day.date === currentDay.value.date)
  )
  const filteredDeviations = computed(() =>
    filterProgressDeviations(
      currentDay.value.deviations,
      selectedCategory.value
    )
  )
  const expandedDeviation = computed(() =>
    currentDay.value.deviations.find(
      (deviation) => deviation.id === expandedDeviationId.value
    )
  )
  const evidenceForView = computed(() => {
    const deviation = expandedDeviation.value
    return deviation
      ? currentDay.value.evidencePhotos.filter((photo) =>
          deviation.evidenceIds.includes(photo.id)
        )
      : currentDay.value.evidencePhotos
  })
  const currentEvidence = computed(
    () =>
      evidenceForView.value.find(
        (photo) => photo.id === selectedEvidenceId.value
      ) ?? evidenceForView.value[0]
  )
  const actualEquipmentCount = computed(() =>
    currentDay.value.equipment.reduce(
      (count, row) => count + row.actualQuantity,
      0
    )
  )
  const plannedEquipmentCount = computed(() =>
    currentDay.value.equipment.reduce(
      (count, row) => count + row.plannedQuantity,
      0
    )
  )
  const equipmentScale = computed(() =>
    Math.max(
      1,
      ...currentDay.value.equipment.flatMap((row) => [
        row.actualQuantity,
        row.plannedQuantity
      ])
    )
  )
  const timingValue = computed(() => {
    const value = currentDay.value.timeDeviationDays
    if (value === null) return 'Не определено'
    if (value === 0) return 'По плану'
    return `${Math.abs(value)} ${Math.abs(value) === 1 ? 'день' : 'дня'}`
  })
  const categoryOptions: { value: ProgressCategory; label: string }[] = [
    { value: 'all', label: 'Все' },
    { value: 'timing', label: 'Сроки' },
    { value: 'equipment', label: 'Техника' }
  ]

  watch(
    projectId,
    async (id) => {
      progressStore.reset()
      selectedDate.value = ''
      selectedCategory.value = 'all'
      expandedDeviationId.value = null
      selectedEvidenceId.value = null
      loadError.value = null
      if (!Number.isFinite(id)) return
      try {
        await progressStore.loadHistory(id)
        selectedDate.value = days.value[days.value.length - 1]?.date ?? ''
      } catch {
        loadError.value = 'Не удалось загрузить аналитику объекта.'
      }
    },
    { immediate: true }
  )
  watch(selectedDate, async (date) => {
    expandedDeviationId.value = null
    selectedEvidenceId.value = null
    if (!date) return
    try {
      await progressStore.loadDetail(projectId.value, date)
    } catch {
      // Summary history remains usable when day details are unavailable.
    }
  })
  watch(selectedCategory, () => {
    expandedDeviationId.value = null
    selectedEvidenceId.value = null
  })
  watch(
    selectedDate,
    async () => {
      await nextTick()
      const container = historyElement.value
      const selected = container?.querySelector<HTMLElement>(
        '[aria-pressed="true"]'
      )
      if (!container || !selected) return
      container.scrollTo({
        left:
          container.scrollLeft +
          selected.getBoundingClientRect().left -
          container.getBoundingClientRect().left -
          (container.clientWidth - selected.clientWidth) / 2,
        behavior: 'instant'
      })
    },
    { immediate: true }
  )

  function moveDay(direction: number): void {
    const day = days.value[selectedDayIndex.value + direction]
    if (day) selectedDate.value = day.date
  }

  function toggleDeviation(id: string): void {
    expandedDeviationId.value = expandedDeviationId.value === id ? null : id
    selectedEvidenceId.value = null
  }

  function showEvidence(): void {
    document.getElementById('dashboard-evidence')?.scrollIntoView({
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches
        ? 'instant'
        : 'smooth',
      block: 'start'
    })
  }

  function equipmentStatus(row: ProgressEquipment): string {
    if (row.deviationType === 'none' || row.deviationType === 'on_plan') {
      return 'По плану'
    }
    if (row.deviationType === 'missing') return 'Не обнаружен'
    if (row.deviationType === 'unexpected') return 'Вне плана'
    return row.delta < 0 ? 'Ниже плана' : 'Выше плана'
  }

  function evidenceTime(date: Date): string {
    return new Intl.DateTimeFormat('ru-RU', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Europe/Moscow'
    }).format(date)
  }
</script>

<template>
  <Teleport defer to="#page-header-actions">
    <v-btn
      :to="{
        name: 'project-snapshots',
        params: { projectId },
        query: { upload: '1' }
      }"
      variant="flat"
      color="primary"
      prepend-icon="mdi-upload"
      >Загрузить фотографии</v-btn
    >
  </Teleport>
  <div class="dashboard">
    <section class="dashboard-intro bw-panel" aria-label="Сводка площадки">
      <div class="dashboard-intro__content">
        <div class="intro-kicker">
          <span class="bw-eyebrow">Площадка под наблюдением</span>
          <span class="demo-tag"
            ><v-icon size="14">mdi-chart-timeline-variant</v-icon> Данные
            мониторинга</span
          >
        </div>
        <h2>{{ project?.name || 'Сводка строительной площадки' }}</h2>
        <p>
          Сопоставляйте наблюдения с планом и проверяйте причины отклонений.
        </p>
        <div class="intro-meta">
          <span v-if="project"
            ><v-icon size="16">mdi-calendar-range-outline</v-icon>
            {{ displayDate(project.startDate) }} —
            {{ displayDate(project.endDate) }}</span
          >
          <span
            ><v-icon size="16">mdi-camera-outline</v-icon> Суточный анализ
            площадки</span
          >
        </div>
      </div>
      <v-btn
        :to="{ name: 'project-plan', params: { projectId } }"
        color="primary"
        variant="flat"
        append-icon="mdi-arrow-top-right"
        class="intro-plan-button"
      >
        Календарный план
      </v-btn>
    </section>

    <div v-if="progressStore.loading.history" class="dashboard-demo-note">
      <v-progress-circular indeterminate size="17" width="2" />
      <span>Загружаем историю наблюдений и отклонений…</span>
    </div>
    <div v-else-if="loadError" class="dashboard-demo-note" role="alert">
      <v-icon size="17">mdi-alert-circle-outline</v-icon>
      <span>{{ loadError }}</span>
    </div>
    <div v-else-if="!days.length" class="dashboard-demo-note">
      <v-icon size="17">mdi-information-outline</v-icon>
      <span>Обработанных наблюдений для этого объекта пока нет.</span>
    </div>

    <section class="day-history bw-panel" aria-labelledby="history-title">
      <div class="panel-heading">
        <div>
          <span class="bw-eyebrow">История наблюдений</span>
          <h3 id="history-title">
            {{
              formatProgressDate(currentDay.date, {
                day: 'numeric',
                month: 'long',
                year: 'numeric'
              })
            }}
          </h3>
        </div>
        <div class="history-navigation">
          <span class="history-count">{{ days.length }} дней</span>
          <v-btn
            icon="mdi-chevron-left"
            variant="text"
            size="small"
            :disabled="selectedDayIndex === 0"
            aria-label="Предыдущий день"
            @click="moveDay(-1)"
          />
          <v-btn
            icon="mdi-chevron-right"
            variant="text"
            size="small"
            :disabled="selectedDayIndex === days.length - 1"
            aria-label="Следующий день"
            @click="moveDay(1)"
          />
        </div>
      </div>
      <div
        ref="historyElement"
        class="history-days"
        role="group"
        aria-label="Выберите день наблюдений"
      >
        <button
          v-for="day in days"
          :key="day.date"
          type="button"
          class="history-day"
          :class="[
            `tone-${day.timingTone}`,
            { 'is-selected': currentDay.date === day.date }
          ]"
          :aria-pressed="currentDay.date === day.date"
          :aria-label="`${formatProgressDate(day.date)}: ${day.timingLabel}`"
          :title="`${formatProgressDate(day.date)} — ${day.timingLabel}`"
          @click="selectedDate = day.date"
        >
          <span class="history-day__weekday">{{
            formatProgressDate(day.date, { weekday: 'short' })
          }}</span>
          <strong>{{
            formatProgressDate(day.date, { day: 'numeric' })
          }}</strong>
          <v-icon size="16">{{ day.timingIcon }}</v-icon>
        </button>
      </div>
      <div class="history-legend">
        <span><i class="legend-dot tone-success"></i>По плану</span>
        <span><i class="legend-dot tone-info"></i>Опережение</span>
        <span><i class="legend-dot tone-warning"></i>Отставание</span>
        <span><i class="legend-dot tone-neutral"></i>Нет оценки</span>
      </div>
    </section>

    <section
      class="summary-grid"
      aria-label="Суточные показатели"
      aria-live="polite"
    >
      <article class="summary-card bw-panel">
        <div class="summary-card__heading">
          <span>Фактический этап</span
          ><v-icon size="20">mdi-layers-triple-outline</v-icon>
        </div>
        <strong class="summary-card__stage">{{
          currentDay.actualStage || 'Не определён'
        }}</strong>
        <p>
          {{
            currentDay.actualStage
              ? currentDay.currentStageScore === null
                ? 'Определён по составу техники'
                : `Соответствие ${(currentDay.currentStageScore * 100).toFixed(0)}%`
              : currentDay.message.text
          }}
        </p>
        <div
          v-if="currentDay.stages.previous || currentDay.stages.next"
          class="stage-probabilities"
        >
          <span v-if="currentDay.stages.previous">
            Предыдущий: {{ currentDay.stages.previous.name }} ·
            {{ Math.round((currentDay.stages.previous.score ?? 0) * 100) }}%
          </span>
          <span v-if="currentDay.stages.next">
            Следующий: {{ currentDay.stages.next.name }} ·
            {{ Math.round((currentDay.stages.next.score ?? 0) * 100) }}%
          </span>
        </div>
      </article>
      <article
        class="summary-card bw-panel"
        :class="`tone-${currentDay.timingTone}`"
      >
        <div class="summary-card__heading">
          <span>Сроки выполнения</span
          ><v-icon size="20">{{ currentDay.timingIcon }}</v-icon>
        </div>
        <strong>{{ timingValue }}</strong>
        <p>{{ currentDay.timingLabel }}</p>
      </article>
      <article class="summary-card bw-panel">
        <div class="summary-card__heading">
          <span>Отклонения</span
          ><v-icon size="20">mdi-alert-circle-outline</v-icon>
        </div>
        <strong>{{
          currentDay.timingStatus === 'unknown'
            ? '—'
            : currentDay.deviationCount
        }}</strong>
        <p>
          {{
            currentDay.timingStatus === 'unknown'
              ? 'Оценка пока недоступна'
              : currentDay.deviationCount
                ? 'Проверьте причины ниже'
                : 'Расхождений не обнаружено'
          }}
        </p>
      </article>
      <article class="summary-card bw-panel">
        <div class="summary-card__heading">
          <span>Качество наблюдений</span
          ><v-icon size="20">mdi-shield-check-outline</v-icon>
        </div>
        <strong class="summary-card__quality">{{
          currentDay.qualityLabel
        }}</strong>
        <p>
          {{ currentDay.usableObservationCount }} из
          {{ currentDay.observationCount }} снимков пригодны для анализа
        </p>
      </article>
    </section>

    <div class="dashboard-columns">
      <section
        class="deviations-panel bw-panel"
        aria-labelledby="deviations-title"
      >
        <div class="panel-heading">
          <div>
            <span class="bw-eyebrow">Точки внимания</span>
            <h3 id="deviations-title">
              Отклонения
              <span class="heading-count">{{
                currentDay.timingStatus === 'unknown'
                  ? '—'
                  : currentDay.deviationCount
              }}</span>
            </h3>
          </div>
          <span class="status-badge" :class="`tone-${currentDay.timingTone}`"
            ><v-icon size="15">{{ currentDay.timingIcon }}</v-icon
            >{{ currentDay.timingLabel }}</span
          >
        </div>
        <div
          class="category-filter"
          role="group"
          aria-label="Категория отклонений"
        >
          <button
            v-for="option in categoryOptions"
            :key="option.value"
            type="button"
            :class="{ 'is-active': selectedCategory === option.value }"
            :aria-pressed="selectedCategory === option.value"
            @click="selectedCategory = option.value"
          >
            {{ option.label }}
            <span>{{
              filterProgressDeviations(currentDay.deviations, option.value)
                .length
            }}</span>
          </button>
        </div>

        <div v-if="!filteredDeviations.length" class="dashboard-empty">
          <div
            class="dashboard-empty__icon"
            :class="
              currentDay.timingStatus === 'unknown'
                ? 'tone-neutral'
                : 'tone-success'
            "
          >
            <v-icon size="27">{{
              currentDay.timingStatus === 'unknown'
                ? 'mdi-image-search-outline'
                : 'mdi-check-all'
            }}</v-icon>
          </div>
          <h4>
            {{
              currentDay.timingStatus === 'unknown'
                ? 'Оценка недоступна'
                : selectedCategory === 'all'
                  ? 'Отклонений нет'
                  : 'В этой категории отклонений нет'
            }}
          </h4>
          <p>
            {{
              currentDay.timingStatus === 'unknown'
                ? currentDay.message.text
                : selectedCategory === 'all'
                  ? 'Наблюдения за выбранный день согласуются с демонстрационным планом.'
                  : 'За этот день нет расхождений по выбранной категории.'
            }}
          </p>
        </div>

        <div v-else class="deviation-list">
          <article
            v-for="deviation in filteredDeviations"
            :key="deviation.id"
            class="deviation-item"
            :class="{ 'is-expanded': expandedDeviationId === deviation.id }"
          >
            <button
              type="button"
              class="deviation-trigger"
              :aria-expanded="expandedDeviationId === deviation.id"
              :aria-controls="`detail-${deviation.id}`"
              @click="toggleDeviation(deviation.id)"
            >
              <span class="deviation-icon"
                ><v-icon size="21">{{ deviation.icon }}</v-icon></span
              >
              <span class="deviation-trigger__copy"
                ><small>{{ deviation.categoryLabel }}</small
                ><strong>{{ deviation.message }}</strong></span
              >
              <v-icon size="20" class="deviation-chevron"
                >mdi-chevron-down</v-icon
              >
            </button>
            <div
              v-if="expandedDeviationId === deviation.id"
              :id="`detail-${deviation.id}`"
              class="deviation-detail"
            >
              <p>{{ deviation.explanation }}</p>
              <dl class="deviation-comparison">
                <div>
                  <dt>По плану</dt>
                  <dd>{{ deviation.expected }}</dd>
                </div>
                <div>
                  <dt>В наблюдениях</dt>
                  <dd>{{ deviation.actual }}</dd>
                </div>
              </dl>
              <v-btn
                v-if="deviation.evidenceIds.length"
                color="primary"
                variant="tonal"
                size="small"
                prepend-icon="mdi-image-multiple-outline"
                @click="showEvidence"
              >
                Посмотреть подтверждения · {{ deviation.evidenceIds.length }}
              </v-btn>
              <p v-else class="deviation-detail__no-evidence">
                Для этого события нет снимков.
              </p>
            </div>
          </article>
        </div>
        <div class="panel-footer">
          <v-icon size="16">mdi-information-outline</v-icon>
          <span
            >Отклонение — повод проверить площадку. Выводы модели требуют
            подтверждения.</span
          >
        </div>
      </section>

      <div class="dashboard-sidebar">
        <section
          class="equipment-panel bw-panel"
          aria-labelledby="equipment-title"
        >
          <div class="panel-heading">
            <div>
              <span class="bw-eyebrow">Состав площадки</span>
              <h3 id="equipment-title">Техника: план и факт</h3>
            </div>
            <v-icon size="23" color="primary">mdi-excavator</v-icon>
          </div>
          <template v-if="currentDay.equipment.length">
            <div class="equipment-totals">
              <div>
                <small>По плану</small
                ><strong>{{ plannedEquipmentCount }} <span>ед.</span></strong>
              </div>
              <span class="equipment-totals__divider"></span>
              <div>
                <small>В наблюдениях</small
                ><strong>{{ actualEquipmentCount }} <span>ед.</span></strong>
              </div>
            </div>
            <table class="equipment-table">
              <caption class="sr-only">
                Количество техники по плану и наблюдениям за выбранный день
              </caption>
              <thead>
                <tr>
                  <th scope="col">Техника</th>
                  <th scope="col">План</th>
                  <th scope="col">Факт</th>
                  <th scope="col">Δ</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in currentDay.equipment"
                  :key="row.techniqueId ?? row.name"
                >
                  <th scope="row">
                    <span class="equipment-name"
                      ><v-icon size="18">{{ row.icon }}</v-icon
                      >{{ row.name }}</span
                    >
                    <div class="equipment-track" aria-hidden="true">
                      <span
                        class="equipment-track__plan"
                        :style="{
                          width: `${(row.plannedQuantity / equipmentScale) * 100}%`
                        }"
                      ></span>
                      <span
                        class="equipment-track__actual"
                        :style="{
                          width: `${(row.actualQuantity / equipmentScale) * 100}%`
                        }"
                      ></span>
                    </div>
                  </th>
                  <td>{{ row.plannedQuantity }}</td>
                  <td>{{ row.actualQuantity }}</td>
                  <td>
                    <span
                      class="equipment-delta"
                      :class="{ 'has-deviation': row.delta !== 0 }"
                      :title="equipmentStatus(row)"
                      >{{ row.delta > 0 ? '+' : ''
                      }}{{ row.delta || '—' }}</span
                    >
                  </td>
                </tr>
              </tbody>
            </table>
            <p class="equipment-note">
              Факт — типичное количество техники в наблюдениях, а не сумма
              детекций на всех снимках. Подтверждения показывают выбранные
              кадры, а не все наблюдения за день.
            </p>
          </template>
          <div v-else class="equipment-unavailable">
            <v-icon size="26">mdi-truck-outline</v-icon>
            <p>
              Количество техники не определено.<br />Нужны пригодные наблюдения.
            </p>
          </div>
        </section>

        <section class="quality-panel bw-panel" aria-labelledby="quality-title">
          <div class="panel-heading">
            <div>
              <span class="bw-eyebrow">Надёжность оценки</span>
              <h3 id="quality-title">Качество данных</h3>
            </div>
            <span
              class="quality-indicator"
              :class="
                currentDay.dataQuality === 'insufficient'
                  ? 'tone-neutral'
                  : currentDay.dataQuality === 'high'
                    ? 'tone-success'
                    : 'tone-warning'
              "
              ><v-icon size="20">{{
                currentDay.dataQuality === 'insufficient'
                  ? 'mdi-help-circle-outline'
                  : 'mdi-shield-check-outline'
              }}</v-icon></span
            >
          </div>
          <div class="quality-metric">
            <span>Пригодные снимки</span
            ><strong
              >{{ currentDay.usableObservationCount }} /
              {{ currentDay.observationCount }}</strong
            >
          </div>
          <div class="quality-bar" aria-hidden="true">
            <span :style="{ width: `${currentDay.coveragePercent}%` }"></span>
          </div>
          <div class="quality-metric">
            <span>Покрытие обработки</span
            ><strong>{{
              currentDay.observationCount
                ? `${currentDay.coveragePercent}%`
                : 'Нет снимков'
            }}</strong>
          </div>
          <div class="quality-metric">
            <span>Согласованность наблюдений</span
            ><strong>{{
              currentDay.agreementPercent === null
                ? 'Не определена'
                : `${currentDay.agreementPercent}%`
            }}</strong>
          </div>
          <ul
            v-if="currentDay.dataQualityReasons.length"
            class="quality-reasons"
          >
            <li v-for="reason in currentDay.dataQualityReasons" :key="reason">
              {{ reason }}
            </li>
          </ul>
          <p v-else class="quality-good">
            <v-icon size="15">mdi-check-circle-outline</v-icon> Наблюдений
            достаточно для суточной оценки.
          </p>
        </section>
      </div>
    </div>

    <section
      id="dashboard-evidence"
      class="evidence-panel bw-panel"
      aria-labelledby="evidence-title"
    >
      <div class="panel-heading">
        <div>
          <span class="bw-eyebrow">От вывода к подтверждению</span>
          <h3 id="evidence-title">
            Снимки площадки
            <span class="heading-count">{{ evidenceForView.length }}</span>
          </h3>
        </div>
        <v-btn
          :to="{
            name: 'project-snapshots',
            params: { projectId },
            query: currentEvidence ? { photoId: currentEvidence.id } : {}
          }"
          variant="text"
          color="primary"
          size="small"
          append-icon="mdi-arrow-right"
        >
          {{ currentEvidence ? 'Открыть снимок в журнале' : 'Открыть журнал' }}
        </v-btn>
      </div>
      <p class="evidence-context">
        {{
          expandedDeviation
            ? `Подтверждения: ${expandedDeviation.message}`
            : 'Выберите снимок, чтобы посмотреть найденную технику и цветовые рамки детекций.'
        }}
      </p>
      <template v-if="currentEvidence">
        <div
          class="evidence-selector"
          role="group"
          aria-label="Выберите подтверждающий снимок"
        >
          <button
            v-for="photo in evidenceForView"
            :key="photo.id"
            type="button"
            :aria-pressed="currentEvidence.id === photo.id"
            :class="{ 'is-active': currentEvidence.id === photo.id }"
            @click="selectedEvidenceId = photo.id"
          >
            <img :src="photo.url" alt="" />
            <span
              ><strong
                >{{ evidenceTime(new Date(photo.capturedAt)) }}
                <small>МСК</small></strong
              ><small
                >{{ photo.detections.length }}
                {{ getObjectWord(photo.detections.length) }}</small
              ></span
            >
            <v-icon
              v-if="currentEvidence.id === photo.id"
              size="18"
              color="primary"
              >mdi-check-circle</v-icon
            >
          </button>
        </div>
        <div class="evidence-caption">
          <span
            ><v-icon size="16">mdi-camera-outline</v-icon>
            {{ formatProgressDate(currentDay.date) }},
            {{ evidenceTime(new Date(currentEvidence.capturedAt)) }} МСК</span
          ><span class="demo-tag">Подтверждение аналитики</span>
        </div>
        <SnapshotExpand
          :key="`${projectId}-${currentDay.date}-${currentEvidence.id}`"
          :snapshot="currentEvidence"
        />
      </template>
      <div v-else class="dashboard-empty evidence-empty">
        <div class="dashboard-empty__icon tone-neutral">
          <v-icon size="28">mdi-image-off-outline</v-icon>
        </div>
        <h4>
          {{
            currentDay.observationCount
              ? 'Нет выбранных подтверждений'
              : 'Нет снимков для подтверждения'
          }}
        </h4>
        <p>
          {{
            currentDay.observationCount
              ? currentDay.message.text
              : 'За выбранный день нет пригодных наблюдений. Отсутствие снимков не означает отсутствие работ на площадке.'
          }}
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
  .dashboard {
    display: flex;
    flex-direction: column;
    gap: 24px;
    color: #182536;
  }

  .dashboard-intro {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    padding: 28px 30px;
    overflow: hidden;
    background: linear-gradient(110deg, #ffffff 50%, #eef4ff 100%);
  }

  .dashboard-intro::before {
    position: absolute;
    inset: 0 auto 0 0;
    width: 4px;
    background: #2563eb;
    content: '';
  }

  .intro-kicker,
  .intro-meta,
  .demo-tag,
  .dashboard-demo-note,
  .panel-heading,
  .history-navigation,
  .history-legend,
  .history-legend > span,
  .summary-card__heading,
  .status-badge,
  .category-filter,
  .deviation-trigger,
  .equipment-name,
  .quality-metric,
  .quality-good,
  .panel-footer,
  .evidence-caption,
  .evidence-caption > span {
    display: flex;
    align-items: center;
  }

  .intro-kicker {
    gap: 14px;
    flex-wrap: wrap;
  }
  .demo-tag {
    gap: 5px;
    width: fit-content;
    padding: 4px 8px;
    border: 1px solid #d8e3f2;
    border-radius: 6px;
    color: #516780;
    background: #f5f8fc;
    font-size: 11px;
    font-weight: 600;
    line-height: 1.35;
  }
  .dashboard-intro h2 {
    margin: 11px 0 8px;
    font-size: 26px;
    line-height: 1.25;
    letter-spacing: -0.7px;
    overflow-wrap: anywhere;
  }
  .dashboard-intro p {
    margin: 0;
    color: #62748b;
    font-size: 14px;
  }
  .intro-meta {
    gap: 20px;
    flex-wrap: wrap;
    margin-top: 18px;
    color: #53667e;
    font-size: 12px;
  }
  .intro-meta > span {
    display: inline-flex;
    align-items: center;
    gap: 7px;
  }
  .intro-plan-button {
    flex-shrink: 0;
  }
  .dashboard-demo-note {
    align-items: flex-start;
    gap: 8px;
    margin: -10px 2px -2px;
    color: #5b6b80;
    font-size: 12px;
    line-height: 1.6;
  }
  .dashboard-demo-note .v-icon {
    margin-top: 2px;
    flex-shrink: 0;
  }

  .day-history,
  .deviations-panel,
  .equipment-panel,
  .quality-panel,
  .evidence-panel {
    padding: 24px;
  }
  .panel-heading {
    justify-content: space-between;
    gap: 14px;
  }
  .panel-heading h3 {
    margin: 6px 0 0;
    font-size: 19px;
    font-weight: 650;
    line-height: 1.25;
    letter-spacing: -0.4px;
  }
  .history-navigation {
    gap: 3px;
  }
  .history-count {
    margin-right: 12px;
    font-size: 12px;
    color: #5b6b80;
    white-space: nowrap;
  }
  .history-days {
    display: grid;
    grid-template-columns: repeat(14, minmax(48px, 1fr));
    gap: 7px;
    margin-top: 22px;
    overflow-x: auto;
    padding: 2px;
  }
  .history-day {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 7px;
    min-height: 94px;
    padding: 11px 5px;
    border: 1px solid #e6ecf4;
    border-radius: 10px;
    color: #64748b;
    background: #f9fbfe;
    cursor: pointer;
    transition:
      background-color 180ms ease,
      border-color 180ms ease,
      transform 180ms ease;
  }
  .history-day:hover {
    border-color: #aec7f5;
    background: #f0f5ff;
    transform: translateY(-2px);
  }
  .history-day__weekday {
    color: #5b6b80;
    font-size: 10px;
    text-transform: uppercase;
  }
  .history-day strong {
    color: #23344b;
    font-size: 19px;
    line-height: 1;
    font-weight: 650;
  }
  .history-day.is-selected {
    border-color: #2563eb;
    background: #edf4ff;
    box-shadow: 0 0 0 1px #2563eb;
  }
  .history-day.is-selected strong,
  .history-day.is-selected .history-day__weekday {
    color: #1d4ed8;
  }
  .history-legend {
    flex-wrap: wrap;
    gap: 18px;
    margin-top: 18px;
    font-size: 11px;
    color: #5b6b80;
  }
  .history-legend > span {
    gap: 6px;
  }
  .legend-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
  }
  .tone-success {
    color: #116b55;
  }
  .tone-info {
    color: #2563eb;
  }
  .tone-warning {
    color: #92550c;
  }
  .tone-neutral {
    color: #5b6b80;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
  }
  .summary-card {
    padding: 22px 23px;
  }
  .summary-card__heading {
    justify-content: space-between;
    gap: 12px;
    color: #61738a;
    font-size: 13px;
  }
  .summary-card__heading .v-icon {
    color: #8a9ab0;
  }
  .summary-card > strong {
    display: block;
    margin-top: 14px;
    color: #182536;
    font-size: 29px;
    line-height: 1.3;
    letter-spacing: -0.6px;
    font-weight: 650;
  }
  .summary-card > .summary-card__stage {
    font-size: 20px;
    letter-spacing: -0.3px;
  }
  .summary-card > .summary-card__quality {
    font-size: 22px;
  }
  .summary-card p {
    margin: 7px 0 0;
    color: #5b6b80;
    font-size: 12px;
    line-height: 1.6;
  }
  .stage-probabilities {
    display: flex;
    flex-direction: column;
    gap: 3px;
    margin-top: 8px;
    color: #65758b;
    font-size: 10px;
    line-height: 1.4;
  }
  .summary-card.tone-warning > strong,
  .summary-card.tone-warning .summary-card__heading .v-icon {
    color: #92550c;
  }
  .summary-card.tone-info > strong,
  .summary-card.tone-info .summary-card__heading .v-icon {
    color: #2563eb;
  }
  .summary-card.tone-success > strong {
    color: #116b55;
    font-size: 25px;
  }
  .summary-card.tone-neutral > strong {
    font-size: 22px;
  }

  .dashboard-columns {
    display: grid;
    grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr);
    align-items: start;
    gap: 24px;
  }
  .dashboard-sidebar {
    display: flex;
    flex-direction: column;
    gap: 24px;
    min-width: 0;
  }
  .heading-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 24px;
    min-height: 24px;
    margin-left: 6px;
    padding: 2px 7px;
    border-radius: 7px;
    background: #f0f4f9;
    color: #5d7089;
    font-size: 12px;
    letter-spacing: 0;
    vertical-align: middle;
  }
  .status-badge {
    gap: 5px;
    max-width: 190px;
    padding: 5px 8px;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 600;
    line-height: 1.4;
  }
  .status-badge.tone-warning {
    background: #fff5e5;
  }
  .status-badge.tone-info {
    background: #eef4ff;
  }
  .status-badge.tone-success {
    background: #ecf8f3;
  }
  .status-badge.tone-neutral {
    background: #f0f4f8;
  }
  .category-filter {
    gap: 4px;
    padding: 4px;
    margin: 22px 0 20px;
    border-radius: 9px;
    background: #f3f6fa;
    width: fit-content;
  }
  .category-filter button {
    border: 0;
    background: transparent;
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 33px;
    padding: 6px 12px;
    border-radius: 6px;
    color: #67788e;
    font-size: 12px;
    cursor: pointer;
    transition:
      color 180ms ease,
      background-color 180ms ease;
  }
  .category-filter button.is-active {
    color: #1d4ed8;
    background: #fff;
    box-shadow: 0 1px 4px #22344a12;
  }
  .category-filter button span {
    font-size: 10px;
  }
  .deviation-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .deviation-item {
    border: 1px solid #e5ebf3;
    border-radius: 10px;
    overflow: hidden;
    transition: border-color 180ms ease;
  }
  .deviation-item:hover {
    border-color: #c5d4e9;
  }
  .deviation-item.is-expanded {
    border-color: #b9cef1;
    background: #fcfdff;
  }
  .deviation-trigger {
    border: 0;
    background: transparent;
    color: inherit;
    gap: 12px;
    width: 100%;
    padding: 17px 14px;
    text-align: left;
    cursor: pointer;
  }
  .deviation-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    width: 37px;
    height: 37px;
    border-radius: 9px;
    background: #fff5e6;
    color: #92550c;
  }
  .deviation-trigger__copy {
    flex: 1;
    min-width: 0;
  }
  .deviation-trigger__copy small {
    display: block;
    margin-bottom: 3px;
    color: #5b6b80;
    font-size: 10px;
  }
  .deviation-trigger__copy strong {
    display: block;
    color: #30425b;
    font-size: 14px;
    line-height: 1.5;
    font-weight: 600;
  }
  .deviation-chevron {
    flex-shrink: 0;
    color: #8293a9;
    transition: transform 180ms ease;
  }
  .is-expanded .deviation-chevron {
    transform: rotate(180deg);
  }
  .deviation-detail {
    padding: 0 18px 20px;
    animation: detail-in 180ms ease both;
  }
  .deviation-detail > p {
    margin: 0;
    color: #64778e;
    font-size: 14px;
    line-height: 1.75;
  }
  .deviation-comparison {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 16px 0;
  }
  .deviation-comparison > div {
    padding: 12px;
    border-radius: 7px;
    background: #f3f6fb;
  }
  .deviation-comparison dt {
    margin-bottom: 5px;
    color: #5b6b80;
    font-size: 11px;
  }
  .deviation-comparison dd {
    color: #30435a;
    font-size: 13px;
    line-height: 1.5;
    font-weight: 600;
  }
  .panel-footer {
    align-items: flex-start;
    gap: 7px;
    padding-top: 22px;
    color: #5b6b80;
    font-size: 10px;
    line-height: 1.6;
  }
  .panel-footer .v-icon {
    margin-top: 1px;
    flex-shrink: 0;
  }
  .dashboard-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 42px 14px;
    text-align: center;
  }
  .dashboard-empty__icon {
    display: grid;
    place-items: center;
    width: 55px;
    height: 55px;
    margin-bottom: 16px;
    border-radius: 16px;
    background: #f1f5fa;
  }
  .dashboard-empty__icon.tone-success {
    background: #ecf8f3;
  }
  .dashboard-empty h4 {
    margin: 0 0 9px;
    font-size: 16px;
    font-weight: 600;
  }
  .dashboard-empty p {
    max-width: 390px;
    margin: 0;
    color: #5b6b80;
    font-size: 14px;
    line-height: 1.7;
  }

  .equipment-totals {
    display: flex;
    gap: 26px;
    margin: 23px 0 21px;
    padding: 16px 19px;
    border-radius: 9px;
    background: #f5f8fd;
  }
  .equipment-totals small {
    display: block;
    margin-bottom: 5px;
    color: #5b6b80;
    font-size: 10px;
  }
  .equipment-totals strong {
    color: #263e5c;
    font-size: 25px;
    font-weight: 650;
  }
  .equipment-totals strong span {
    color: #5b6b80;
    font-size: 12px;
    font-weight: 400;
  }
  .equipment-totals__divider {
    width: 1px;
    background: #e0e8f3;
  }
  .equipment-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
  }
  .equipment-table th {
    font-weight: 500;
  }
  .equipment-table thead th {
    padding: 0 6px 10px;
    color: #5b6b80;
    font-size: 10px;
  }
  .equipment-table th:not(:first-child),
  .equipment-table td {
    text-align: center;
    width: 45px;
  }
  .equipment-table tbody th,
  .equipment-table td {
    border-top: 1px solid #edf1f7;
    padding: 14px 6px;
  }
  .equipment-table tbody th {
    width: auto;
  }
  .equipment-name {
    gap: 8px;
    color: #42556e;
    font-size: 14px;
  }
  .equipment-name .v-icon {
    color: #8b9ab0;
  }
  .equipment-table td {
    color: #3c5270;
    font-size: 13px;
    font-weight: 600;
  }
  .equipment-delta {
    display: inline-flex;
    justify-content: center;
    min-width: 25px;
    padding: 3px 5px;
    color: #5b6b80;
    font-size: 11px;
    border-radius: 5px;
  }
  .equipment-delta.has-deviation {
    color: #92550c;
    background: #fff3df;
  }
  .equipment-track {
    position: relative;
    height: 4px;
    max-width: 140px;
    margin: 8px 0 0 26px;
  }
  .equipment-track span {
    position: absolute;
    height: 4px;
    top: 0;
    left: 0;
    border-radius: 3px;
  }
  .equipment-track__plan {
    background: #dce6f5;
  }
  .equipment-track__actual {
    background: #5b8de7;
    max-width: 100%;
  }
  .equipment-note {
    margin: 15px 0 0;
    color: #5b6b80;
    font-size: 10px;
    line-height: 1.7;
  }
  .equipment-unavailable {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 30px 8px 12px;
    color: #5b6b80;
  }
  .equipment-unavailable p {
    font-size: 12px;
    line-height: 1.7;
  }
  .quality-panel .panel-heading {
    margin-bottom: 22px;
  }
  .quality-panel .panel-heading h3 {
    font-size: 17px;
  }
  .quality-indicator {
    display: grid;
    place-items: center;
    width: 34px;
    height: 34px;
    border-radius: 9px;
    background: #f2f6fa;
  }
  .quality-metric {
    justify-content: space-between;
    gap: 14px;
    margin: 12px 0;
    color: #5b6b80;
    font-size: 12px;
  }
  .quality-metric strong {
    color: #40546d;
    font-size: 12px;
    text-align: right;
    font-weight: 600;
  }
  .quality-bar {
    height: 5px;
    margin: 11px 0 18px;
    overflow: hidden;
    border-radius: 5px;
    background: #edf1f7;
  }
  .quality-bar span {
    display: block;
    height: 100%;
    background: #3b82c6;
    border-radius: inherit;
    transition: width 200ms ease;
  }
  .quality-reasons {
    list-style: none;
    margin: 18px 0 0;
    padding: 12px 14px;
    border-radius: 8px;
    background: #f6f8fb;
  }
  .quality-reasons li {
    position: relative;
    padding-left: 11px;
    margin: 4px 0;
    color: #5b6b80;
    font-size: 12px;
    line-height: 1.7;
  }
  .quality-reasons li::before {
    position: absolute;
    left: 0;
    top: 7px;
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: #9cacc0;
    content: '';
  }
  .quality-good {
    gap: 7px;
    margin: 20px 0 0;
    color: #116b55;
    font-size: 12px;
    line-height: 1.6;
  }

  .evidence-panel {
    scroll-margin-top: 100px;
  }
  .evidence-context {
    margin: 12px 0 20px;
    color: #5b6b80;
    font-size: 14px;
    line-height: 1.6;
  }
  .evidence-selector {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 22px;
  }
  .evidence-selector button {
    background: #fff;
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 8px;
    min-width: 190px;
    border: 1px solid #e1e8f1;
    border-radius: 9px;
    text-align: left;
    cursor: pointer;
    transition:
      border-color 180ms ease,
      background-color 180ms ease;
  }
  .evidence-selector button.is-active {
    border-color: #78a2ed;
    background: #f0f5ff;
  }
  .evidence-selector button img {
    width: 58px;
    height: 40px;
    object-fit: cover;
    border-radius: 5px;
    background: #e6edf5;
  }
  .evidence-selector button > span {
    display: flex;
    flex-direction: column;
    gap: 3px;
    flex: 1;
  }
  .evidence-selector strong {
    color: #354e71;
    font-size: 13px;
    font-weight: 600;
  }
  .evidence-selector strong small {
    margin-left: 3px;
    font-weight: 400;
  }
  .evidence-selector small {
    color: #5b6b80;
    font-size: 11px;
  }
  .evidence-caption {
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    margin: 0 0 13px;
    color: #5b6b80;
    font-size: 11px;
  }
  .evidence-caption > span {
    gap: 6px;
  }
  .evidence-empty {
    padding: 34px 14px;
  }
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  button:focus-visible {
    outline: 3px solid #93b5f6;
    outline-offset: 3px;
  }
  @keyframes detail-in {
    from {
      opacity: 0;
      transform: translateY(-4px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @media (min-width: 1600px) {
    .dashboard-columns {
      grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
    }
  }
  @media (max-width: 1050px) {
    .summary-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .dashboard-columns {
      grid-template-columns: 1fr;
    }
    .dashboard-sidebar {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      align-items: start;
    }
    .history-days {
      grid-template-columns: repeat(14, minmax(48px, 1fr));
    }
    .dashboard-intro {
      align-items: flex-start;
    }
    .intro-plan-button {
      margin-top: 9px;
    }
  }
  @media (max-width: 767px) {
    .dashboard {
      gap: 18px;
    }
    .dashboard-intro {
      flex-direction: column;
      padding: 22px;
      gap: 16px;
    }
    .dashboard-intro h2 {
      font-size: 23px;
    }
    .dashboard-intro p {
      font-size: 12px;
      line-height: 1.7;
    }
    .intro-plan-button {
      margin: 0;
    }
    .intro-kicker {
      gap: 10px;
    }
    .intro-meta {
      gap: 9px;
      margin-top: 14px;
      font-size: 11px;
    }
    .dashboard-demo-note {
      font-size: 10px;
      margin: -6px 2px 0;
    }
    .day-history,
    .deviations-panel,
    .equipment-panel,
    .quality-panel,
    .evidence-panel {
      padding: 19px;
    }
    .panel-heading {
      gap: 9px;
    }
    .panel-heading h3 {
      font-size: 17px;
    }
    .history-count {
      display: none;
    }
    .history-days {
      margin-top: 18px;
      gap: 7px;
      padding-bottom: 10px;
    }
    .history-day {
      min-height: 86px;
    }
    .history-legend {
      gap: 10px 15px;
      margin-top: 9px;
      font-size: 10px;
    }
    .summary-grid {
      grid-template-columns: 1fr;
      gap: 12px;
    }
    .summary-card {
      padding: 17px 15px;
    }
    .summary-card__heading {
      font-size: 11px;
      align-items: flex-start;
    }
    .summary-card__heading .v-icon {
      font-size: 17px !important;
    }
    .summary-card > strong {
      font-size: 26px;
      margin-top: 12px;
    }
    .summary-card > .summary-card__stage {
      font-size: 17px;
    }
    .summary-card > .summary-card__quality,
    .summary-card.tone-neutral > strong {
      font-size: 17px;
    }
    .summary-card.tone-success > strong {
      font-size: 21px;
    }
    .summary-card p {
      font-size: 11px;
    }
    .dashboard-columns {
      gap: 18px;
    }
    .dashboard-sidebar {
      display: flex;
      gap: 18px;
    }
    .status-badge {
      max-width: 130px;
      font-size: 9px;
    }
    .category-filter button {
      padding: 6px 10px;
      font-size: 11px;
    }
    .deviation-trigger {
      padding: 14px 11px;
      gap: 10px;
    }
    .deviation-trigger__copy strong {
      font-size: 13px;
    }
    .deviation-detail {
      padding: 0 14px 17px;
    }
    .deviation-comparison {
      gap: 9px;
    }
    .deviation-comparison > div {
      padding: 10px;
    }
    .evidence-panel .panel-heading {
      align-items: flex-start;
      flex-direction: column;
    }
    .evidence-panel .panel-heading .v-btn {
      margin-left: -10px;
    }
    .evidence-selector {
      flex-wrap: nowrap;
      overflow-x: auto;
      padding: 2px 2px 8px;
      margin-bottom: 17px;
    }
    .evidence-selector button {
      flex-shrink: 0;
      min-width: 187px;
    }
    .evidence-caption {
      font-size: 10px;
    }
  }
  @media (max-width: 380px) {
    .summary-grid {
      grid-template-columns: 1fr;
    }
    .deviations-panel > .panel-heading {
      align-items: flex-start;
      flex-direction: column;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      animation: none !important;
      transition: none !important;
    }
    .history-day:hover {
      transform: none;
    }
  }
</style>
