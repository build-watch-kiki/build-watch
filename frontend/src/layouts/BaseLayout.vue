<script setup lang="ts">
  import BrandMark from '@/components/BrandMark.vue'
</script>

<template>
  <v-app>
    <header class="base-header">
      <div class="base-header__inner">
        <BrandMark light />
        <span class="base-header__divider" />
        <span class="base-header__caption">Мониторинг строительства</span>
        <span class="base-header__tag"
          ><v-icon icon="mdi-office-building-outline" size="16" /> Рабочее
          пространство</span
        >
      </div>
    </header>
    <v-main>
      <router-view />
    </v-main>
    <footer class="base-footer">
      <span>BuildWatch</span>
      <span>Мониторинг строительной площадки</span>
    </footer>
  </v-app>
</template>

<style scoped>
  .base-header {
    background: #142033;
    padding: 21px 32px;
  }
  .base-header__inner {
    max-width: 1360px;
    margin: auto;
    display: flex;
    align-items: center;
    gap: 22px;
  }
  .base-header__divider {
    width: 1px;
    height: 25px;
    background: #ffffff24;
  }
  .base-header__caption {
    font-size: 13px;
    color: #becbdf;
  }
  .base-header__tag {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 8px;
    color: #d3def0;
    font-size: 12px;
  }
  .base-footer {
    max-width: 1424px;
    width: 100%;
    margin: auto;
    padding: 24px 32px;
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #65758b;
  }
  @media (max-width: 767px) {
    .base-header {
      padding: 18px 20px;
    }
    .base-header__caption,
    .base-header__divider,
    .base-header__tag {
      display: none;
    }
    .base-footer {
      padding: 24px 20px;
    }
  }
</style>
