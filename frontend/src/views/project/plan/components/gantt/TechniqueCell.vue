<script setup lang="ts">
  import type { Stage } from '@/types/plan'
  import { getTotalTechnique } from '@/utils/plan.ts'

  defineProps<{ stage: Stage }>()
</script>

<template>
  <v-menu
    v-if="getTotalTechnique(stage) > 0"
    location="bottom"
    :close-on-content-click="true"
  >
    <template #activator="{ props }">
      <button
        v-bind="props"
        class="gantt__tech-link"
        type="button"
        :aria-label="`Техника этапа ${stage.workTypeName}. Количество машин: ${getTotalTechnique(stage)}`"
      >
        {{ getTotalTechnique(stage) }} ед.
      </button>
    </template>
    <v-card min-width="260" density="compact">
      <v-list density="compact">
        <v-list-item v-for="req in stage.requiresTechnique" :key="req.id">
          <v-list-item-title>
            {{ req.nameRu || req.name }}
          </v-list-item-title>
          <template #append>
            <span class="text-medium-emphasis text-no-wrap ml-4">
              {{ req.quantity }} ед.
            </span>
          </template>
        </v-list-item>
      </v-list>
    </v-card>
  </v-menu>
  <span v-else>—</span>
</template>

<style scoped>
  .gantt__tech-link {
    color: rgb(var(--v-theme-primary));
    background: #eff5ff;
    border: none;
    border-radius: 7px;
    padding: 5px 7px;
    font: inherit;
    font-weight: 600;
    cursor: pointer;
  }
  .gantt__tech-link:hover {
    background: #e0ebff;
  }
  .gantt__tech-link:focus-visible {
    outline: 2px solid #2563eb;
    outline-offset: 2px;
  }
</style>
