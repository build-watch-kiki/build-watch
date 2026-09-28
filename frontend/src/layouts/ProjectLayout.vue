<script setup lang="ts">
  import { ref, computed, onMounted, watch } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useDisplay } from 'vuetify'
  import { useProjectsStore } from '@/store/projects'
  import type { NavItem } from '@/types/navigation'
  import { displayDate } from '@/utils/datetime'
  import { getApiErrorDetail } from '@/utils/errors'
  import BrandMark from '@/components/BrandMark.vue'

  const props = defineProps<{ projectId: string }>()
  const route = useRoute()
  const router = useRouter()
  const { width } = useDisplay()
  const mobileNavigation = computed(() => width.value < 1280)
  const drawer = ref(!mobileNavigation.value)
  const rail = ref(false)
  const projectsStore = useProjectsStore()
  const detail = computed(() =>
    projectsStore.getDetail?.id === Number(props.projectId)
      ? projectsStore.getDetail
      : null
  )
  const loading = computed(() => projectsStore.getLoadingState)
  const detailError = ref<string | null>(null)
  const navItems = computed<NavItem[]>(() => {
    const base = `/projects/${props.projectId}`
    return [
      {
        title: 'Мониторинг',
        icon: 'mdi-view-dashboard-outline',
        to: `${base}/dashboard`,
        name: 'project-dashboard'
      },
      {
        title: 'Журнал наблюдений',
        icon: 'mdi-image-multiple-outline',
        to: `${base}/log`,
        name: 'project-snapshots'
      },
      {
        title: 'Календарный план',
        icon: 'mdi-calendar-month-outline',
        to: `${base}/plan`,
        name: 'project-plan'
      },
      {
        title: 'Справочник',
        icon: 'mdi-book-open-outline',
        to: `${base}/reference`,
        name: 'project-reference'
      }
    ]
  })
  const currentTitle = computed(() => (route.meta.title as string) || 'Проект')
  const pageDescriptions: Record<string, string> = {
    'project-dashboard': 'Состояние объекта, отклонения и подтверждения',
    'project-snapshots': 'Наблюдения с площадки и распознанная техника',
    'project-plan': 'Этапы работ, сроки и потребность в технике',
    'project-reports': 'Результаты мониторинга в одном месте',
    'project-reference': 'Виды работ и строительная техника'
  }
  const currentDescription = computed(
    () => pageDescriptions[String(route.name)] || ''
  )
  async function loadDetail() {
    const id = Number(props.projectId)
    detailError.value = null
    try {
      await projectsStore.loadDetail({ projectId: id })
    } catch (error) {
      if (id === Number(props.projectId))
        detailError.value = getApiErrorDetail(
          error,
          'Не удалось загрузить объект'
        )
    }
  }
  function toggleDrawer() {
    if (mobileNavigation.value) drawer.value = !drawer.value
    else rail.value = !rail.value
  }
  function goToProjects() {
    void router.push({ name: 'projects' })
  }
  const sectionChunkWarmers: Record<string, () => Promise<unknown>> = {
    'project-dashboard': () =>
      import('@/views/project/dashboard/Dashboard.vue'),
    'project-snapshots': () =>
      import('@/views/project/snapshots/Snapshots.vue'),
    'project-plan': () => import('@/views/project/plan/Plan.vue'),
    'project-reference': () => import('@/views/project/reference/Reference.vue')
  }
  const warmedSections = new Set<string>()
  function warmSection(name: string) {
    if (warmedSections.has(name)) return
    warmedSections.add(name)
    void sectionChunkWarmers[name]?.().catch(() => undefined)
  }
  onMounted(() => {
    void loadDetail()
  })
  watch(
    () => props.projectId,
    () => {
      void loadDetail()
    }
  )
  watch(mobileNavigation, (mobile) => {
    drawer.value = !mobile
  })
  watch(
    () => route.fullPath,
    () => {
      if (mobileNavigation.value) drawer.value = false
    }
  )
</script>

<template>
  <v-app>
    <v-navigation-drawer
      v-model="drawer"
      :rail="rail && !mobileNavigation"
      :temporary="mobileNavigation"
      :permanent="!mobileNavigation"
      width="264"
      rail-width="76"
      class="project-nav"
      color="secondary"
    >
      <div class="project-nav__brand">
        <BrandMark
          light
          :compact="rail && !mobileNavigation"
          role="button"
          @click="goToProjects"
        />
      </div>
      <v-list class="project-nav__back" nav>
        <v-list-item
          prepend-icon="mdi-arrow-left"
          title="Все объекты"
          @click="goToProjects"
        />
      </v-list>
      <div v-if="!rail || mobileNavigation" class="project-nav__context">
        <span class="project-nav__label">Текущий объект</span>
        <strong v-if="detail">{{ detail.name }}</strong>
        <span v-else>{{
          loading.detail ? 'Загрузка объекта…' : `Объект #${projectId}`
        }}</span>
        <small v-if="detail">{{ detail.projectType?.name }}</small>
      </div>
      <v-list nav class="project-nav__links">
        <v-list-item
          v-for="item in navItems"
          :key="item.name"
          :prepend-icon="item.icon"
          :title="item.title"
          :to="item.to"
          :active="route.name === item.name"
          rounded="lg"
          @mouseenter="warmSection(item.name)"
          @focus="warmSection(item.name)"
        />
      </v-list>
      <template #append>
        <div v-if="!rail || mobileNavigation" class="project-nav__footer">
          <v-icon icon="mdi-ruler-square" size="20" />
          <div>
            <strong>Контроль на каждом этапе</strong
            ><span>План · Наблюдения · Аналитика</span>
          </div>
        </div>
      </template>
    </v-navigation-drawer>
    <v-app-bar elevation="0" height="76" class="project-topbar">
      <v-btn
        :icon="
          mobileNavigation ? 'mdi-menu' : rail ? 'mdi-menu-open' : 'mdi-menu'
        "
        variant="text"
        aria-label="Переключить навигацию"
        @click="toggleDrawer"
      />
      <div class="project-topbar__context">
        <div class="project-topbar__breadcrumb">
          <span>Объекты</span
          ><v-icon icon="mdi-chevron-right" size="15" /><strong>{{
            detail?.name || `Объект #${projectId}`
          }}</strong>
        </div>
        <span v-if="detail" class="project-topbar__dates"
          >{{ displayDate(detail.startDate) }} —
          {{ displayDate(detail.endDate) }}</span
        >
      </div>
      <template #append
        ><span v-if="detail" class="project-topbar__type"
          ><v-icon icon="mdi-office-building-outline" size="17" />{{
            detail.projectType?.name
          }}</span
        ></template
      >
      <v-progress-linear
        v-if="loading.detail"
        absolute
        location="bottom"
        indeterminate
        color="primary"
        height="2"
      />
    </v-app-bar>
    <v-main class="project-main">
      <div class="project-content">
        <div class="page-heading">
          <div>
            <p class="bw-eyebrow">Рабочее пространство</p>
            <h1>{{ currentTitle }}</h1>
            <p class="bw-page-lead">{{ currentDescription }}</p>
          </div>
          <div id="page-header-actions" class="page-heading__actions"></div>
        </div>
        <v-alert
          v-if="detailError"
          type="error"
          variant="tonal"
          class="mb-5"
          title="Объект недоступен"
        >
          {{ detailError }}
          <div class="mt-3">
            <v-btn size="small" variant="outlined" @click="loadDetail"
              >Повторить</v-btn
            >
          </div>
        </v-alert>
        <div
          v-if="!detail && !detailError"
          class="bw-panel project-wait"
          role="status"
        >
          <v-progress-circular indeterminate color="primary" size="20" /><span
            >Загружаем данные объекта…</span
          >
        </div>
        <router-view v-if="!detailError" :key="projectId" />
      </div>
    </v-main>
  </v-app>
</template>

<style scoped>
  .project-nav {
    border-right: none !important;
  }
  .project-nav__brand {
    height: 76px;
    padding: 19px 23px;
    border-bottom: 1px solid #ffffff0d;
  }
  .project-nav__back {
    margin: 14px 10px 4px;
    background: transparent;
    color: #c0ccdf;
  }
  .project-nav__context {
    margin: 12px 23px 28px;
    display: flex;
    flex-direction: column;
    gap: 9px;
  }
  .project-nav__label {
    color: #a0b2ca;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.3px;
  }
  .project-nav__context strong {
    font-weight: 600;
    font-size: 14px;
    line-height: 1.55;
    overflow-wrap: anywhere;
  }
  .project-nav__context small {
    color: #a0b2ca;
    font-size: 12px;
  }
  .project-nav__links {
    background: transparent;
    margin: 0 10px;
  }
  .project-nav__links :deep(.v-list-item) {
    color: #c3cee0;
    margin-bottom: 7px;
    min-height: 48px;
  }
  .project-nav__links :deep(.v-list-item--active) {
    background: #2563eb;
    color: #fff;
  }
  .project-nav__links :deep(.v-list-item__overlay) {
    opacity: 0;
  }
  .project-nav__links :deep(.v-list-item__prepend > .v-icon) {
    margin-inline-end: 16px;
    opacity: 1;
  }
  .project-nav__links :deep(.v-list-item-title) {
    font-weight: 500;
    font-size: 13px;
  }
  .project-nav__footer {
    margin: 20px 22px 28px;
    padding-top: 24px;
    border-top: 1px solid #ffffff14;
    display: flex;
    gap: 12px;
    color: #b5c4da;
  }
  .project-nav__footer strong {
    display: block;
    font-size: 11px;
    font-weight: 550;
    margin-bottom: 5px;
  }
  .project-nav__footer span {
    display: block;
    font-size: 10px;
    color: #a0b2ca;
  }
  .project-topbar {
    border-bottom: 1px solid #e1e7ef;
  }
  .project-topbar__context {
    margin-left: 12px;
    min-width: 0;
  }
  .project-topbar__breadcrumb {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
  }
  .project-topbar__breadcrumb > span {
    color: #65758b;
  }
  .project-topbar__breadcrumb strong {
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .project-topbar__dates {
    display: block;
    font-size: 11px;
    color: #65758b;
    margin-top: 5px;
  }
  .project-topbar__type {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 28px;
    color: #5b6b80;
    font-size: 12px;
    max-width: 220px;
  }
  .project-content {
    max-width: 1680px;
    margin: auto;
    padding: 32px;
    min-width: 0;
  }
  .project-main {
    min-width: 0;
  }
  .page-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 26px;
  }
  .page-heading h1 {
    margin: 5px 0 6px;
    font-size: 29px;
    line-height: 1.3;
    font-weight: 650;
    letter-spacing: -0.8px;
  }
  .page-heading__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    flex-shrink: 0;
  }
  .project-wait {
    padding: 14px 20px;
    margin-bottom: 16px;
    display: flex;
    justify-content: flex-start;
    align-items: center;
    gap: 12px;
    color: #5b6b80;
    font-size: 13px;
  }
  @media (max-width: 767px) {
    .project-content {
      padding: 24px 16px;
    }
    .page-heading {
      align-items: flex-start;
      flex-direction: column;
      gap: 16px;
      margin-bottom: 20px;
    }
    .page-heading h1 {
      font-size: 25px;
    }
    .project-topbar__type {
      display: none;
    }
    .project-topbar__breadcrumb > span,
    .project-topbar__breadcrumb > .v-icon {
      display: none;
    }
    .project-topbar__context {
      margin-left: 4px;
      padding-right: 16px;
    }
  }
</style>
