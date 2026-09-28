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
  <div class="no-data-placeholder">
    <v-icon :size="props.size === 'small' ? 36 : 56" color="disabled">
      mdi-database-off-outline
    </v-icon>
    <span
      v-if="props.showText"
      class="no-data-placeholder__text font-weight-bold"
      :style="{ fontSize: props.size === 'small' ? '14px' : '21px' }"
    >
      <slot>
        {{ props.text }}
      </slot>
    </span>
  </div>
</template>
<style scoped>
  .no-data-placeholder {
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
</style>
