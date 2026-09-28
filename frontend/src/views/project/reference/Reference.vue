<script setup lang="ts">
  import { computed, ref } from 'vue'
  import { useRoute } from 'vue-router'

  import ReferenceCatalogTab from './components/ReferenceCatalogTab.vue'

  const route = useRoute()
  const projectId = computed(() => Number(route.params.projectId))

  const tab = ref<'workTypes' | 'techniques' | 'projectTypes'>('workTypes')

  const tabs = [
    {
      value: 'projectTypes',
      title: 'Типы проектов',
      icon: 'mdi-format-list-bulleted-type',
      description:
        'Типы объектов строительства. Выбираются один раз при создании проекта и определяют его категорию в общем списке.'
    },
    {
      value: 'workTypes',
      title: 'Виды работ',
      icon: 'mdi-tools',
      description:
        'Виды строительных работ этого проекта. Используются при создании этапов календарного плана и для сопоставления состава техники в мониторинге.'
    },
    {
      value: 'techniques',
      title: 'Строительная техника',
      icon: 'mdi-excavator',
      description:
        'Техника, которую распознаёт модель на снимках. Русское название показывается в интерфейсе, системное имя используется в данных детекций и привязке к этапам.'
    }
  ] as const
</script>

<template>
  <div class="reference">
    <section class="bw-panel reference-intro" aria-label="О справочнике">
      <div>
        <span class="bw-eyebrow">База знаний проекта</span>
        <h2>Справочник</h2>
        <p class="bw-muted">
          Здесь собраны все каталоги, на которые опираются календарный план и
          мониторинг: виды работ, строительная техника и типы проектов. Найдите
          нужный элемент через поиск — данные подгружаются постранично.
        </p>
        <div class="reference-intro__hints">
          <span
            ><v-icon size="16">mdi-magnify</v-icon>Поиск работает по
            названию</span
          >
          <span
            ><v-icon size="16">mdi-calendar-month-outline</v-icon>Виды работ
            задаются на этапе</span
          >
          <span
            ><v-icon size="16">mdi-cctv</v-icon>Техника распознаётся на
            снимках</span
          >
        </div>
      </div>
    </section>

    <section class="bw-panel reference-docs" aria-label="Нормативные документы">
      <div class="reference-docs__icon" aria-hidden="true">
        <v-icon icon="mdi-file-pdf-box" size="40" color="primary" />
      </div>
      <div>
        <span class="bw-eyebrow">Документы</span>
        <h3>Нормативные документы</h3>
        <p class="bw-muted">
          Сюда попадут регламенты, паспорта техники и методички в PDF — всё, на
          что опирается приёмка работ и разбор отклонений.
        </p>
        <v-btn color="primary" variant="tonal" disabled>
          Раздел скоро появится
        </v-btn>
      </div>
    </section>

    <section class="bw-panel reference-catalogs" aria-label="Каталоги">
      <v-tabs v-model="tab" color="primary" class="mb-4">
        <v-tab
          v-for="item in tabs"
          :key="item.value"
          :value="item.value"
          :prepend-icon="item.icon"
        >
          {{ item.title }}
        </v-tab>
      </v-tabs>

      <v-tabs-window v-model="tab">
        <v-tabs-window-item
          v-for="item in tabs"
          :key="item.value"
          :value="item.value"
        >
          <ReferenceCatalogTab
            :catalog="item.value"
            :project-id="projectId"
            :description="item.description"
          />
        </v-tabs-window-item>
      </v-tabs-window>

      <p class="bw-muted reference-catalogs__note">
        <v-icon size="15">mdi-information-outline</v-icon>
        Каталоги ведутся на стороне сервиса: содержимое здесь только для
        просмотра и доступно только для чтения.
      </p>
    </section>
  </div>
</template>

<style scoped>
  .reference {
    display: grid;
    gap: 24px;
  }

  .reference-intro {
    padding: 24px;
  }

  .reference-intro h2 {
    margin: 6px 0 8px;
    font-size: 24px;
    letter-spacing: -0.5px;
  }

  .reference-intro p {
    max-width: 640px;
    font-size: 15px;
    line-height: 1.7;
  }

  .reference-intro__hints {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 20px;
    margin-top: 16px;
    color: #5b6b80;
    font-size: 13px;
  }

  .reference-intro__hints > span {
    display: inline-flex;
    align-items: center;
    gap: 7px;
  }

  .reference-catalogs {
    overflow: hidden;
    padding: 8px 24px 24px;
  }

  .reference-catalogs__note {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    margin: 20px 0 0;
    font-size: 12px;
    line-height: 1.6;
  }

  .reference-docs {
    display: flex;
    gap: 20px;
    align-items: flex-start;
    padding: 24px;
  }

  .reference-docs__icon {
    display: grid;
    place-items: center;
    flex-shrink: 0;
    width: 72px;
    height: 72px;
    border-radius: 16px;
    background: #eef4ff;
  }

  .reference-docs h3 {
    margin: 6px 0 8px;
    font-size: 19px;
  }

  .reference-docs p {
    max-width: 560px;
    margin-bottom: 16px;
    font-size: 14px;
    line-height: 1.7;
  }

  @media (max-width: 767px) {
    .reference-intro,
    .reference-catalogs,
    .reference-docs {
      padding: 19px 16px;
    }

    .reference-docs {
      flex-direction: column;
    }
  }
</style>
