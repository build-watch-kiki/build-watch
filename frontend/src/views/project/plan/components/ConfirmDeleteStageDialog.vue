<script setup lang="ts">
  import { computed } from 'vue'
  import ConfirmActionDialog from '@/components/ConfirmActionDialog.vue'
  import type { Stage } from '@/types/plan'
  import { cutString } from '@/utils/string'

  interface Props {
    open: boolean
    loading: boolean
    error: string | null
    stage: Stage | null
  }

  const props = defineProps<Props>()

  const emit = defineEmits<{
    confirm: []
    cancel: []
  }>()

  const displayName = computed(() => {
    if (!props.stage?.workTypeName) return ''
    return cutString(props.stage.workTypeName, 30)
  })

  const labels = computed(() => ({
    title: 'Удалить этап?',
    text: props.stage
      ? `Вы уверены, что хотите удалить этап «${displayName.value || 'Без названия'}»? Это действие нельзя отменить.`
      : 'Вы уверены, что хотите удалить этап?'
  }))
</script>

<template>
  <ConfirmActionDialog
    :open="props.open"
    :loading="props.loading"
    :error="props.error"
    :labels="labels"
    @confirm="emit('confirm')"
    @cancel="emit('cancel')"
  />
</template>
