<script setup lang="ts">
  import type { Project } from '@/types/projects'
  import { displayDate } from '@/utils/datetime'
  import { getProjectTypeIcon } from '@/utils/projectTypes'
  import { useProjectsStore } from '@/store/projects'
  const cardProps = defineProps<{ project: Project }>()
  const emit = defineEmits<{ delete: []; edit: [] }>()

  let warmed = false
  function warmProject() {
    if (warmed) return
    warmed = true
    // Chunk + данные греются до клика, чтобы первый переход был мгновенным.
    void import('@/layouts/ProjectLayout.vue').catch(() => undefined)
    void import('@/views/project/dashboard/Dashboard.vue').catch(
      () => undefined
    )
    void useProjectsStore()
      .loadDetail({ projectId: cardProps.project.id })
      .catch(() => undefined)
  }
</script>

<template>
  <article
    class="project-card bw-panel"
    @mouseenter="warmProject"
    @focusin="warmProject"
  >
    <div class="project-card__top">
      <span class="project-card__icon"
        ><v-icon
          :icon="getProjectTypeIcon(project.projectType?.id)"
          size="24"
        ></v-icon></span
      ><span class="project-card__id"
        >Объект / {{ String(project.id).padStart(3, '0') }}</span
      ><v-menu
        ><template #activator="{ props }"
          ><v-btn
            v-bind="props"
            icon="mdi-dots-horizontal"
            size="small"
            variant="text"
            :aria-label="`Действия с объектом ${project.name}`" /></template
        ><v-list
          ><v-list-item
            title="Редактировать объект"
            prepend-icon="mdi-pencil-outline"
            @click="emit('edit')" /><v-list-item
            title="Удалить объект"
            prepend-icon="mdi-delete-outline"
            class="text-error"
            @click="emit('delete')" /></v-list
      ></v-menu>
    </div>
    <router-link
      :to="`/projects/${project.id}/dashboard`"
      class="project-card__name"
      :title="project.name"
      >{{ project.name }}</router-link
    >
    <p class="project-card__type">
      {{ project.projectType?.name || 'Строительный объект' }}
    </p>
    <div class="project-card__schedule">
      <span class="project-card__schedule-label"
        ><v-icon icon="mdi-calendar-range-outline" size="16" />Плановые
        сроки</span
      ><strong
        >{{ displayDate(project.startDate) }}<span>—</span
        >{{ displayDate(project.endDate) }}</strong
      >
    </div>
    <div class="project-card__bottom">
      <router-link :to="`/projects/${project.id}/log`">Фотографии</router-link
      ><v-btn
        :to="`/projects/${project.id}/dashboard`"
        color="primary"
        variant="tonal"
        append-icon="mdi-arrow-right"
        >Мониторинг</v-btn
      >
    </div>
  </article>
</template>

<style scoped>
  .project-card {
    display: flex;
    flex-direction: column;
    padding: 23px;
    min-width: 0;
    transition:
      border-color 0.18s ease,
      box-shadow 0.18s ease;
  }
  .project-card:hover {
    border-color: #b6c9ec;
    box-shadow: 0 8px 28px #14203308;
  }
  .project-card__top {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
  }
  .project-card__icon {
    width: 44px;
    height: 44px;
    background: #edf3ff;
    color: #2563eb;
    display: grid;
    place-items: center;
    border-radius: 12px;
    flex-shrink: 0;
  }
  .project-card__id {
    color: #65758b;
    font-size: 14px;
    letter-spacing: 0.5px;
  }
  .project-card__top .v-btn {
    margin-left: auto;
    color: #5b6b80;
  }
  .project-card__name {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    color: #182536;
    font-size: 22px;
    font-weight: 650;
    line-height: 1.5;
    letter-spacing: -0.4px;
    overflow-wrap: anywhere;
  }
  .project-card__name:hover {
    color: #2563eb;
  }
  .project-card__type {
    color: #5b6b80;
    font-size: 15px;
    margin: 8px 0 16px;
  }
  .project-card__schedule {
    margin-top: auto;
    padding: 17px 0 22px;
    border-top: 1px solid #e8edf4;
  }
  .project-card__schedule-label {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 14px;
    color: #65758b;
    margin-bottom: 8px;
  }
  .project-card__schedule strong {
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 550;
    font-size: 16px;
    font-variant-numeric: tabular-nums;
    flex-wrap: wrap;
  }
  .project-card__schedule strong > span {
    color: #8a99ad;
  }
  .project-card__bottom {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding-top: 17px;
    border-top: 1px solid #e8edf4;
  }
  .project-card__bottom > a:not(.v-btn) {
    font-size: 15px;
    color: #5b6b80;
  }
  .project-card__bottom :deep(.v-btn) {
    font-size: 15px;
  }
  .project-card__bottom > a:not(.v-btn):hover {
    color: #2563eb;
  }
</style>
