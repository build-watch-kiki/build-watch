<script setup lang="ts">
  import { computed, onMounted, ref } from 'vue'
  import { useProjectsStore } from '@/store/projects'
  import CreateProjectDialog from './components/CreateProjectDialog.vue'
  import DeleteProjectConfirmDialog from './components/DeleteProjectConfirmDialog.vue'
  import ProjectCard from './components/ProjectCard.vue'
  import type { Project } from '@/types/projects'
  import type { CreateProjectPayload } from '@/types/projects.actions'
  import { getApiErrorDetail } from '@/utils/errors'
  import router from '@/router'
  import { useDisplay } from 'vuetify'

  const projectsStore = useProjectsStore()
  const { width } = useDisplay()
  const steps = [
    {
      icon: 'mdi-office-building-plus-outline',
      title: 'Создайте объект',
      text: 'Укажите название, тип и сроки'
    },
    {
      icon: 'mdi-calendar-month-outline',
      title: 'Заполните план',
      text: 'Добавьте этапы работ и технику'
    },
    {
      icon: 'mdi-camera-outline',
      title: 'Загрузите фотографии',
      text: 'Посмотрите распознавание в журнале'
    }
  ]
  const pageSize = 15
  const currentPage = ref(1)
  const list = computed(() => projectsStore.getList)
  const loading = computed(() => projectsStore.getLoadingState)
  const pagination = computed(() => projectsStore.getPagination)
  const listError = ref<string | null>(null)
  const actionError = ref<string | null>(null)
  const scrollKey = ref(0)
  const isInitialLoading = computed(
    () => loading.value.list && list.value.length === 0
  )
  const selectedItem = ref<Project | null>(null)
  const showModals = ref<Record<string, boolean>>({
    create: false,
    delete: false
  })
  async function loadInitialList() {
    currentPage.value = 1
    listError.value = null
    try {
      await projectsStore.loadPaginatedList({
        page: currentPage.value,
        pageSize
      })
      scrollKey.value++
    } catch (error) {
      listError.value = getApiErrorDetail(error, 'Не удалось загрузить объекты')
    }
  }
  async function loadMore({
    done
  }: {
    done: (status: 'ok' | 'empty' | 'error') => void
  }) {
    if (!pagination.value) {
      done('empty')
      return
    }
    const nextPage = currentPage.value + 1
    if (nextPage > pagination.value.totalPages) {
      done('empty')
      return
    }
    try {
      currentPage.value = nextPage
      await projectsStore.loadPaginatedList({ page: nextPage, pageSize }, true)
      done(currentPage.value < pagination.value.totalPages ? 'ok' : 'empty')
    } catch {
      currentPage.value = nextPage - 1
      done('error')
    }
  }
  function openActionDialog(action: string, project: Project | null) {
    selectedItem.value = project
    actionError.value = null
    showModals.value[action] = true
  }
  async function handleDeleteConfirm() {
    if (!selectedItem.value) return
    actionError.value = null
    try {
      await projectsStore.deleteItem({ projectId: selectedItem.value.id })
      showModals.value.delete = false
      selectedItem.value = null
      await loadInitialList()
    } catch (error) {
      actionError.value = getApiErrorDetail(error, 'Не удалось удалить объект')
    }
  }
  function handleDeleteCancel() {
    selectedItem.value = null
    showModals.value.delete = false
    actionError.value = null
  }
  async function handleCreateOk(data: CreateProjectPayload) {
    actionError.value = null
    try {
      const newId = await projectsStore.createItem(data)
      if (!newId) return
      await router.push(`/projects/${newId}/plan`)
      showModals.value.create = false
    } catch (error) {
      actionError.value = getApiErrorDetail(error, 'Не удалось создать объект')
    }
  }
  function handleCreateCancel() {
    showModals.value.create = false
    actionError.value = null
  }
  onMounted(() => {
    void loadInitialList()
  })
</script>

<template>
  <div class="projects-page bw-entrance">
    <section class="projects-intro">
      <h1>Мониторинг строительной площадки</h1>
      <p>
        Выберите объект, чтобы открыть план работ, загрузить фотографии и
        посмотреть результаты распознавания.
      </p>
    </section>
    <details class="workflow-card bw-panel" :open="width >= 768">
      <summary>
        <span>Как начать работу</span
        ><v-icon icon="mdi-chevron-down" size="20" />
      </summary>
      <ol class="workflow-card__steps">
        <li v-for="(step, index) in steps" :key="step.title">
          <span class="workflow-card__number">0{{ index + 1 }}</span>
          <div>
            <strong>{{ step.title }}</strong>
            <p>{{ step.text }}</p>
          </div>
          <v-icon :icon="step.icon" size="22" />
        </li>
      </ol>
    </details>
    <section id="objects" class="objects-section">
      <div class="objects-heading">
        <div>
          <div class="objects-heading__title">
            <h2>Строительные объекты</h2>
            <span v-if="pagination" class="objects-count">{{
              pagination.total
            }}</span>
          </div>
          <p class="bw-page-lead">Ваши проекты и сроки строительства.</p>
        </div>
        <v-btn
          color="primary"
          variant="flat"
          size="large"
          prepend-icon="mdi-plus"
          @click="openActionDialog('create', null)"
          >Создать объект</v-btn
        >
      </div>
      <div
        v-if="isInitialLoading"
        class="projects-skeleton"
        role="status"
        aria-label="Загрузка объектов"
      >
        <v-skeleton-loader
          v-for="index in 3"
          :key="index"
          type="heading, paragraph, actions"
          class="bw-panel"
        />
      </div>
      <v-alert
        v-if="listError"
        type="error"
        variant="tonal"
        title="Не удалось загрузить объекты"
        class="mb-4"
        >{{ listError }}
        <div class="mt-3">
          <v-btn variant="outlined" size="small" @click="loadInitialList"
            >Повторить</v-btn
          >
        </div></v-alert
      >
      <div
        v-if="!list.length && !loading.list && !listError"
        class="empty-objects bw-panel"
      >
        <span class="empty-objects__icon"
          ><v-icon icon="mdi-office-building-plus-outline" size="32"
        /></span>
        <h3>Начните с первого объекта</h3>
        <p>
          Создайте проект и добавьте этапы работ.<br />Так у мониторинга
          появится план для сравнения.
        </p>
        <v-btn
          color="primary"
          variant="flat"
          prepend-icon="mdi-plus"
          @click="openActionDialog('create', null)"
          >Создать объект</v-btn
        >
      </div>
      <v-infinite-scroll
        v-if="list.length"
        :key="scrollKey"
        :disabled="!pagination || currentPage >= pagination.totalPages"
        class="project-scroll"
        @load="loadMore"
      >
        <div class="projects-grid">
          <ProjectCard
            v-for="project in list"
            :key="project.id"
            :project="project"
            @delete="openActionDialog('delete', project)"
          />
        </div>
        <template #loading
          ><div v-if="loading.list" class="scroll-status" role="status">
            <v-progress-circular indeterminate size="22" color="primary" /><span
              >Загружаем объекты…</span
            >
          </div></template
        >
        <template #empty
          ><p class="objects-loaded">Все объекты загружены</p></template
        >
        <template #error="{ props }"
          ><div class="scroll-status">
            <span>Не удалось загрузить следующую страницу.</span
            ><v-btn v-bind="props" variant="text" color="primary"
              >Повторить</v-btn
            >
          </div></template
        >
      </v-infinite-scroll>
    </section>
    <CreateProjectDialog
      :open="showModals.create"
      :loading="loading.action"
      :error="actionError"
      @ok="handleCreateOk"
      @cancel="handleCreateCancel"
    />
    <DeleteProjectConfirmDialog
      :open="showModals.delete"
      :loading="loading.action"
      :error="actionError"
      :project="selectedItem"
      @confirm="handleDeleteConfirm"
      @cancel="handleDeleteCancel"
    />
  </div>
</template>

<style scoped>
  .projects-page {
    max-width: 1424px;
    margin: auto;
    padding: 24px 32px;
  }
  .projects-intro {
    margin-bottom: 20px;
  }
  .projects-intro h1 {
    font-size: clamp(28px, 2.5vw, 36px);
    line-height: 1.3;
    font-weight: 650;
    letter-spacing: -0.7px;
  }
  .projects-intro p {
    max-width: 840px;
    color: #5b6b80;
    font-size: 17px;
    line-height: 1.65;
    margin-top: 12px;
  }
  .objects-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    margin-bottom: 16px;
  }
  .objects-heading__title {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
  }
  .objects-heading h2 {
    font-size: 24px;
    font-weight: 650;
  }
  .objects-heading .bw-page-lead {
    font-size: 16px;
  }
  .objects-count {
    padding: 3px 10px;
    background: #e5edf9;
    color: #34527e;
    font-size: 15px;
    border-radius: 7px;
  }
  .projects-grid,
  .projects-skeleton {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 22px;
  }
  .project-scroll {
    overflow: visible;
  }
  .workflow-card {
    padding: 16px 20px;
    margin-bottom: 20px;
  }
  .workflow-card summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    font-size: 15px;
    color: #5b6b80;
    font-weight: 600;
    list-style: none;
  }
  .workflow-card summary::-webkit-details-marker {
    display: none;
  }
  .workflow-card summary:focus-visible {
    outline: 3px solid #2563eb;
    outline-offset: 4px;
  }
  .workflow-card[open] summary .v-icon {
    transform: rotate(180deg);
  }
  .workflow-card__steps {
    list-style: none;
    padding: 0;
    margin: 14px 0 0;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 24px;
  }
  .workflow-card__steps li {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
  }
  .workflow-card__steps strong {
    font-size: 16px;
  }
  .workflow-card__steps p {
    font-size: 14px;
    line-height: 1.5;
    color: #5b6b80;
    margin: 4px 0 0;
  }
  .workflow-card__number {
    color: #2563eb;
    font-size: 14px;
    font-weight: 700;
  }
  .workflow-card__steps .v-icon {
    color: #65758b;
    margin-left: auto;
  }
  .empty-objects {
    text-align: center;
    padding: 40px 24px;
  }
  .empty-objects__icon {
    display: inline-grid;
    place-items: center;
    width: 64px;
    height: 64px;
    border-radius: 16px;
    color: #2563eb;
    background: #edf3ff;
    margin-bottom: 18px;
  }
  .empty-objects h3 {
    font-size: 24px;
    margin-bottom: 12px;
  }
  .empty-objects p {
    color: #5b6b80;
    font-size: 16px;
    line-height: 1.7;
    margin-bottom: 24px;
  }
  .scroll-status {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
    padding: 22px;
    color: #5b6b80;
    font-size: 15px;
    flex-wrap: wrap;
  }
  .objects-loaded {
    text-align: center;
    color: #65758b;
    font-size: 14px;
    padding: 18px;
  }
  @media (max-width: 1100px) {
    .projects-grid,
    .projects-skeleton {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }
  @media (max-width: 767px) {
    .projects-page {
      padding: 24px 16px;
    }
    .projects-intro {
      margin-bottom: 24px;
    }
    .projects-grid,
    .projects-skeleton {
      grid-template-columns: 1fr;
      gap: 16px;
    }
    .objects-heading {
      align-items: flex-start;
      flex-direction: column;
      gap: 16px;
    }
    .workflow-card {
      padding: 16px;
      margin-bottom: 24px;
    }
    .workflow-card__steps {
      grid-template-columns: 1fr;
      gap: 16px;
    }
    .workflow-card__steps li + li {
      padding-top: 14px;
      border-top: 1px solid #e1e7ef;
    }
  }
</style>
