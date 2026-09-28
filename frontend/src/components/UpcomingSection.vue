<script setup lang="ts">
  import { computed } from 'vue'
  import { useRoute } from 'vue-router'
  const props = defineProps<{ kind: 'reports' | 'reference' }>()
  const route = useRoute()
  const content = computed(() =>
    props.kind === 'reports'
      ? {
          icon: 'mdi-chart-box-outline',
          title: 'Отчёты появятся здесь',
          description:
            'Здесь можно будет просматривать сводки по срокам, технике и отклонениям за выбранный период.',
          action: 'Открыть мониторинг',
          destination: 'dashboard',
          features: [
            'Сводка по объекту',
            'История отклонений',
            'Подтверждения наблюдений'
          ]
        }
      : {
          icon: 'mdi-book-open-outline',
          title: 'Справочник готовится',
          description:
            'В этом разделе будут собраны виды строительных работ и техника, необходимые для календарного плана.',
          action: 'Открыть календарный план',
          destination: 'plan',
          features: ['Виды работ', 'Строительная техника', 'Ресурсы этапов']
        }
  )
</script>

<template>
  <section class="upcoming bw-panel bw-entrance">
    <div class="upcoming__illustration" aria-hidden="true">
      <div class="upcoming__grid" />
      <v-icon :icon="content.icon" size="52" />
    </div>
    <span class="bw-chip">Раздел в разработке</span>
    <h2>{{ content.title }}</h2>
    <p>{{ content.description }}</p>
    <div class="upcoming__features">
      <span v-for="feature in content.features" :key="feature"
        ><v-icon icon="mdi-check-circle-outline" size="16" />{{ feature }}</span
      >
    </div>
    <v-btn
      color="primary"
      variant="flat"
      append-icon="mdi-arrow-right"
      :to="`/projects/${route.params.projectId}/${content.destination}`"
      >{{ content.action }}</v-btn
    >
  </section>
</template>

<style scoped>
  .upcoming {
    min-height: 490px;
    padding: 52px 24px;
    text-align: center;
    display: flex;
    align-items: center;
    flex-direction: column;
  }
  .upcoming__illustration {
    position: relative;
    display: grid;
    place-items: center;
    width: 190px;
    height: 120px;
    margin-bottom: 24px;
    color: #2563eb;
  }
  .upcoming__illustration .v-icon {
    background: #edf3ff;
    padding: 20px;
    box-sizing: content-box;
    border: 8px solid #fff;
    border-radius: 26px;
    z-index: 1;
  }
  .upcoming__grid {
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(#e5ecf7 1px, transparent 1px),
      linear-gradient(90deg, #e5ecf7 1px, transparent 1px);
    background-size: 20px 20px;
    mask-image: radial-gradient(ellipse, #000, transparent 75%);
  }
  .upcoming h2 {
    font-size: 26px;
    font-weight: 650;
    letter-spacing: -0.6px;
    margin: 20px 0 12px;
  }
  .upcoming p {
    max-width: 530px;
    font-size: 14px;
    line-height: 1.8;
    color: #5b6b80;
  }
  .upcoming__features {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 18px;
    margin: 24px 0 32px;
    color: #5b6b80;
  }
  .upcoming__features > span {
    display: flex;
    gap: 7px;
    align-items: center;
    font-size: 12px;
  }
  @media (max-width: 767px) {
    .upcoming {
      padding: 36px 20px;
    }
    .upcoming h2 {
      font-size: 23px;
    }
    .upcoming__features {
      flex-direction: column;
      text-align: left;
      gap: 12px;
    }
  }
</style>
