<script setup lang="ts">
  withDefaults(defineProps<{ compact?: boolean; light?: boolean }>(), {
    compact: false,
    light: false
  })
</script>

<template>
  <span class="brand" :class="{ 'brand--light': light }">
    <span class="brand__mark" aria-hidden="true">
      <svg viewBox="0 0 32 32" fill="none">
        <path
          d="M8 24V13M16 24V8M24 24V17"
          stroke="currentColor"
          stroke-width="3"
          stroke-linecap="round"
        />
        <path
          d="m6 9 9-5 11 7"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </span>
    <span v-if="!compact" class="brand__name">Build<span>Watch</span></span>
  </span>
</template>

<style scoped>
  .brand {
    display: inline-flex;
    align-items: center;
    gap: 11px;
    white-space: nowrap;
  }
  .brand__mark {
    width: 38px;
    height: 38px;
    display: grid;
    place-items: center;
    border-radius: 11px;
    background: #2563eb;
    color: #fff;
  }
  .brand__mark svg {
    width: 29px;
    height: 29px;
  }
  .brand__name {
    font-size: 21px;
    font-weight: 750;
    letter-spacing: -0.7px;
    color: #182536;
  }
  .brand__name > span {
    font-weight: 450;
  }
  .brand--light .brand__name {
    color: #fff;
  }
</style>
