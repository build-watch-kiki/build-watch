<script setup lang="ts">
  import { computed } from 'vue'
  import LoadingPlaceholder from '@/components/LoadingPlaceholder.vue'

  interface Props {
    open: boolean
    loading: boolean
    error: string | null
    labels?: {
      title?: string
      text?: string
      confirm?: string
      cancel?: string
    }
  }

  const props = defineProps<Props>()

  const defaultLabels = {
    title: 'Подтвердите действие',
    text: '',
    confirm: 'Подтвердить',
    cancel: 'Отмена'
  }

  const labels = computed(() => ({
    ...defaultLabels,
    ...props.labels
  }))

  const emit = defineEmits<{
    confirm: []
    cancel: []
  }>()

  function onUpdateModelValue(value: boolean) {
    if (!value) emit('cancel')
  }
</script>

<template>
  <v-dialog
    :model-value="props.open"
    width="480"
    @update:model-value="onUpdateModelValue"
  >
    <v-card class="dialog-card">
      <v-card-title class="confirm-heading">
        <span class="confirm-heading__icon"
          ><v-icon icon="mdi-alert-outline" size="26"
        /></span>
        <h2>
          {{ labels.title }}
        </h2>
      </v-card-title>

      <loading-placeholder
        v-if="props.loading"
        size="small"
        text="Выполняется..."
      />

      <v-card-text v-else class="dialog-content">
        <div v-if="labels.text" class="dialog-text">
          {{ labels.text }}
        </div>

        <v-alert v-if="props.error" class="mt-4" type="error" variant="tonal">
          {{ props.error }}
        </v-alert>
      </v-card-text>

      <v-card-actions class="dialog-actions">
        <v-btn variant="text" @click="emit('cancel')">
          {{ labels.cancel }}
        </v-btn>

        <v-spacer />

        <v-btn
          variant="flat"
          color="error"
          :loading="props.loading"
          :disabled="props.loading"
          @click="emit('confirm')"
        >
          {{ labels.confirm }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
  .dialog-card {
    max-height: 800px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .dialog-content {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    padding: 0 28px 24px;
  }

  .confirm-heading {
    padding: 28px 28px 16px;
    white-space: normal;
  }
  .confirm-heading h2 {
    font-size: 21px;
    font-weight: 650;
    line-height: 1.4;
    margin-top: 18px;
  }
  .confirm-heading__icon {
    display: grid;
    place-items: center;
    width: 50px;
    height: 50px;
    border-radius: 14px;
    color: #b42318;
    background: #fff0ed;
  }

  .dialog-text {
    overflow-wrap: anywhere;
    font-size: 14px;
    line-height: 1.8;
    color: #5b6b80;
  }

  .dialog-actions {
    flex: 0 0 auto;
    padding: 18px 28px;
    border-top: 1px solid #e1e7ef;
    background: #fafbfd;
  }

  .dialog-actions :deep(.v-btn),
  .dialog-actions :deep(.v-btn__content) {
    font-size: 14px;
    text-transform: none;
  }
</style>
