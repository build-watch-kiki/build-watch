<script setup lang="ts">
  import NotFoundPlaceholder from '@/components/NotFoundPlaceholder.vue'
</script>
<template>
  <section class="not-found-page bw-panel">
    <NotFoundPlaceholder size="large" text="Страница не найдена" />
    <p>Проверьте адрес или вернитесь к строительным объектам.</p>
    <v-btn
      to="/projects"
      color="primary"
      variant="flat"
      prepend-icon="mdi-arrow-left"
      >Все объекты</v-btn
    >
  </section>
</template>
<style scoped>
  .not-found-page {
    max-width: 620px;
    margin: 60px auto;
    padding: 45px 24px;
    text-align: center;
  }
  .not-found-page p {
    margin: 12px 0 24px;
    color: #5b6b80;
    font-size: 14px;
    line-height: 1.7;
  }
  @media (max-width: 767px) {
    .not-found-page {
      margin: 24px 16px;
    }
  }
</style>
