<script setup lang="ts">
  import { ref, watch } from 'vue'
  import DataFormDialog from '@/components/DataFormDialog.vue'
  import CatalogSelector from '@/components/CatalogSelector.vue'
  import type { Stage } from '@/types/plan'
  import type { PaginatedCatalog } from '@/types/catalogs'
  import type { Technique } from '@/store/variants'
  import NoDataPlaceholder from '@/components/NoDataPlaceholder.vue'

  interface Props {
    open: boolean
    loading: boolean
    error: string | null
    stage: Stage | null
    techniquesCatalog: PaginatedCatalog<Technique>
  }

  const props = defineProps<Props>()

  const emit = defineEmits<{
    ok: [techniques: { name: string; quantity: number }[]]
    cancel: []
  }>()

  interface Row {
    name: string | null
    quantity: number
  }

  const techniques = ref<Row[]>([])
  const formRef = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(
    null
  )

  const dataObject = ref<Record<string, unknown>>({
    techniques: techniques.value
  })

  watch(
    () => props.open,
    (open) => {
      if (open) {
        techniques.value = (props.stage?.requiresTechnique || []).map((r) => ({
          name: r.name,
          quantity: r.quantity
        }))
        dataObject.value = {
          techniques: techniques.value
        } as unknown as Record<string, unknown>
      }
    }
  )

  watch(
    techniques,
    (val) => {
      dataObject.value = { techniques: val } as unknown as Record<
        string,
        unknown
      >
    },
    { deep: true }
  )

  function updateQuantity(row: Row, value: unknown) {
    const quantity = Number(value)

    row.quantity = Number.isFinite(quantity)
      ? Math.max(1, Math.trunc(quantity))
      : 1
  }

  function addRow() {
    techniques.value.push({ name: null, quantity: 1 })
  }

  function removeRow(idx: number) {
    techniques.value.splice(idx, 1)
  }

  async function handleOk() {
    const result = await formRef.value?.validate()
    if (result && !result.valid) return
    const filtered = techniques.value
      .filter((t) => t.name && t.name.trim() && t.quantity > 0)
      .map((t) => ({ name: t.name!.trim(), quantity: Number(t.quantity) }))
    emit('ok', filtered)
  }

  function handleCancel() {
    emit('cancel')
  }
</script>

<template>
  <DataFormDialog
    :open="props.open"
    :loading="props.loading"
    :error="props.error"
    :data-object="dataObject"
    :labels="{ title: 'Требования к технике' }"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <v-form ref="formRef" @submit.prevent>
      <p class="stage-technique__context">{{ props.stage?.workTypeName }}</p>
      <no-data-placeholder v-if="techniques.length === 0" size="small">
        Техника пока не добавлена. Укажите машины, необходимые на период этапа.
      </no-data-placeholder>
      <v-row
        v-for="(row, idx) in techniques"
        :key="idx"
        no-gutters
        class="d-flex align-center stage-technique__row"
      >
        <v-col cols="12" sm="8">
          <CatalogSelector
            v-model="row.name"
            :catalog="props.techniquesCatalog"
            :selected-item="
              (props.stage?.requiresTechnique.find(
                (r) => r.name === row.name
              ) as unknown as Technique) ||
              (row.name
                ? ({ name: row.name, nameRu: row.name } as unknown as Technique)
                : null)
            "
            placeholder="Выберите технику"
            :disabled="props.loading"
            :allow-search="true"
            :clearable="false"
            item-value="name"
            item-title="nameRu"
            class="flex-grow-1"
          />
        </v-col>
        <v-col cols="10" sm="3">
          <v-text-field
            :model-value="row.quantity"
            type="number"
            label="Количество"
            variant="outlined"
            density="comfortable"
            class="stage-technique__quantity"
            min="1"
            step="1"
            :disabled="props.loading"
            @update:model-value="updateQuantity(row, $event)"
          />
        </v-col>
        <v-col cols="2" sm="1" class="text-right">
          <v-btn
            icon="mdi-close"
            :aria-label="`Убрать технику из строки ${idx + 1}`"
            variant="text"
            class="mb-6"
            :disabled="props.loading"
            @click="removeRow(idx)"
          />
        </v-col>
      </v-row>
    </v-form>
    <template #actions>
      <v-btn
        variant="tonal"
        color="primary"
        prepend-icon="mdi-plus"
        :disabled="props.loading"
        @click="addRow"
      >
        Добавить технику
      </v-btn>
    </template>
  </DataFormDialog>
</template>

<style scoped>
  .stage-technique__context {
    margin: 0 0 20px;
    font-size: 14px;
    line-height: 1.6;
    color: #53647a;
    overflow-wrap: anywhere;
  }
  .stage-technique__row {
    border-top: 1px solid #e0e7f0;
    padding-top: 16px;
  }
  .stage-technique__quantity {
    padding-left: 12px;
  }
  @media (max-width: 599px) {
    .stage-technique__quantity {
      padding-left: 0;
    }
  }
</style>
