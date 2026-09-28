<script setup lang="ts">
  import { computed } from 'vue'

  interface Props {
    open: boolean
    loading: boolean
    dataObject: Record<string, unknown>
    defaultData?: Record<string, unknown>
    error: string | null
    labels?: {
      title?: string
      ok?: string
      cancel?: string
    }
  }

  const props = defineProps<Props>()

  const defaultLabels = {
    title: 'Заполните форму',
    text: '',
    ok: 'Сохранить',
    cancel: 'Отмена'
  }

  const labels = computed(() => ({
    ...defaultLabels,
    ...props.labels
  }))

  const emit = defineEmits<{
    ok: []
    cancel: []
  }>()

  function onUpdateModelValue(value: boolean) {
    if (!value) emit('cancel')
  }
</script>

<template>
  <v-dialog
    :model-value="props.open"
    width="560"
    @update:model-value="onUpdateModelValue"
  >
    <v-card class="dialog-card">
      <v-card-title class="dialog-heading">
        <p class="bw-eyebrow">BuildWatch / {{ labels.ok }}</p>
        <h2>{{ labels.title }}</h2>
      </v-card-title>

      <v-card-text class="dialog-content">
        <slot :data="dataObject"></slot>

        <v-alert v-if="props.error" class="mt-4" type="error" variant="tonal">
          {{ props.error }}
        </v-alert>
      </v-card-text>

      <v-card-actions class="dialog-actions">
        <slot name="actions" />

        <v-spacer />

        <v-btn variant="text" @click="emit('cancel')">
          {{ labels.cancel }}
        </v-btn>

        <v-btn
          variant="flat"
          color="primary"
          :loading="props.loading"
          :disabled="props.loading"
          @click="emit('ok')"
        >
          {{ labels.ok }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
  .dialog-card {
    max-height: min(800px, calc(100dvh - 48px));
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .dialog-content {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    padding: 8px 28px 16px;
  }

  .dialog-heading {
    padding: 26px 28px 18px;
    white-space: normal;
  }
  .dialog-heading h2 {
    margin: 8px 0 0;
    font-size: 22px;
    line-height: 1.4;
    font-weight: 650;
    letter-spacing: -0.5px;
  }

  .dialog-actions {
    flex: 0 0 auto;
    flex-wrap: wrap;
    padding: 18px 28px;
    border-top: 1px solid #e1e7ef;
    background: #fafbfd;
  }

  .dialog-actions :deep(.v-btn) {
    font-size: 14px;
    text-transform: none;
  }
  @media (max-width: 600px) {
    .dialog-heading {
      padding: 22px 20px 16px;
    }
    .dialog-content {
      padding: 8px 20px 16px;
    }
    .dialog-actions {
      padding: 16px 20px;
    }
    .dialog-actions :deep(.v-btn:first-child:nth-last-child(4)) {
      flex-basis: 100%;
      margin-bottom: 8px;
    }
  }
</style>
