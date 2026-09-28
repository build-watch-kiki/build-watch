<script setup lang="ts">
  interface Props {
    size?: 'small' | 'large'
    text?: string
    showText?: boolean
  }

  const props = withDefaults(defineProps<Props>(), {
    size: 'small',
    text: 'Ничего не найдено',
    showText: true
  })
</script>

<template>
  <div class="not-found-placeholder">
    <v-icon :size="props.size === 'small' ? 32 : 56" color="primary">
      mdi-file-search-outline
    </v-icon>

    <span
      v-if="props.showText"
      class="not-found-placeholder__text font-weight-bold text-center"
      :style="{ fontSize: props.size === 'small' ? '14px' : '21px' }"
    >
      {{ props.text }}
    </span>
  </div>
</template>

<style scoped>
  .not-found-placeholder {
    width: 100%;
    height: auto;
    min-height: auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 24px 16px;
    color: #5b6b80;
    line-height: 1.6;
  }

  .not-found-placeholder__text {
    max-width: 600px;
  }
</style>
