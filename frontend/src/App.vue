<script setup lang="ts">
  import router from '@/router'
  import {
    dismissNavigationError,
    failedTarget,
    isNavigating,
    navigationError
  } from '@/utils/navigation'

  function retryNavigation() {
    const target = failedTarget.value
    dismissNavigationError()
    if (target) void router.replace(target)
  }
</script>

<template>
  <div
    v-if="isNavigating"
    class="route-loading"
    role="status"
    aria-label="Загрузка раздела"
  >
    <v-progress-linear indeterminate color="primary" height="3" />
  </div>
  <div v-if="navigationError" class="route-error">
    <v-alert type="error" variant="tonal" title="Не удалось открыть раздел">
      {{ navigationError }}
      <div class="mt-3">
        <v-btn size="small" variant="outlined" @click="retryNavigation"
          >Повторить</v-btn
        >
        <v-btn
          size="small"
          variant="text"
          class="ml-2"
          @click="dismissNavigationError"
          >Закрыть</v-btn
        >
      </div>
    </v-alert>
  </div>
  <router-view />
</template>

<style scoped>
  .route-loading {
    position: fixed;
    top: 0;
    right: 0;
    left: 0;
    z-index: 3000;
  }
  .route-error {
    position: fixed;
    right: 16px;
    bottom: 16px;
    z-index: 3000;
    max-width: min(420px, calc(100vw - 32px));
  }
</style>
