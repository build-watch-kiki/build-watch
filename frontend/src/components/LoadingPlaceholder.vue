<script setup lang="ts">
  interface Props {
    size?: 'small' | 'large'
    text?: string
    showText?: boolean
  }

  const props = withDefaults(defineProps<Props>(), {
    size: 'small',
    text: 'Загрузка данных...',
    showText: true
  })
</script>
<template>
  <div class="loading-placeholder">
    <v-progress-circular
      indeterminate
      :size="props.size === 'small' ? 24 : 36"
      :width="props.size === 'small' ? 3 : 3"
      color="primary"
    />
    <span
      v-if="props.showText"
      class="loading-placeholder__text font-weight-bold"
      :style="{ fontSize: props.size === 'small' ? '13px' : '15px' }"
    >
      {{ props.text }}
    </span>
  </div>
</template>
<style scoped>
  .loading-placeholder {
    width: 100%;
    height: auto;
    min-height: auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 14px;
    padding: 24px 16px;
    color: #5b6b80;
  }
</style>
