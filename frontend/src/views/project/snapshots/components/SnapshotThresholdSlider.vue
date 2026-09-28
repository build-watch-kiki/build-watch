<script setup lang="ts">
  interface Props {
    modelValue: number
  }

  const props = defineProps<Props>()

  const emit = defineEmits<{
    'update:modelValue': [value: number]
  }>()

  function onUpdate(value: number) {
    emit('update:modelValue', value)
  }
</script>

<template>
  <div class="snapshot-threshold">
    <div class="text-body-2 font-weight-medium mb-1">
      Порог уверенности: {{ props.modelValue }}%
    </div>
    <v-slider
      :model-value="props.modelValue"
      :min="1"
      :max="99"
      :step="1"
      thumb-label
      hide-details
      color="primary"
      @update:model-value="onUpdate"
    />
  </div>
</template>
