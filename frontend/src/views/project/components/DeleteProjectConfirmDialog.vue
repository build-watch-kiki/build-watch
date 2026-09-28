<script setup lang="ts">
  import type { Project } from '@/types/projects.ts'
  import ConfirmActionDialog from '@/components/ConfirmActionDialog.vue'

  interface Props {
    open: boolean
    project: Project | null
    loading: boolean
    error: string | null
  }

  const props = defineProps<Props>()

  const emit = defineEmits<{
    confirm: []
    cancel: []
  }>()
</script>

<template>
  <confirm-action-dialog
    :open="props.open"
    :labels="{
      title: 'Удалить строительный объект?',
      confirm: 'Удалить объект',
      text: `Удалить объект «${props.project?.name || ''}» и связанные с ним данные? Это действие нельзя отменить.`
    }"
    :loading="props.loading"
    :error="props.error"
    @confirm="emit('confirm')"
    @cancel="emit('cancel')"
  />
</template>
