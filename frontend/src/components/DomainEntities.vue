<script setup>
defineProps({ entities: Array })
</script>

<template>
  <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-3">
    <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">DOMAIN ENTITIES</span>
    <div class="flex flex-wrap gap-2">
      <span
        v-for="entity in entities"
        :key="entity"
        class="font-mono text-xs text-accent bg-accent/10 px-3 py-1 rounded-full"
      >
        {{ entity.split(' (')[0] }}
      </span>
    </div>
    <p v-if="!entities?.length" class="text-sm text-text-muted">No domain entities detected.</p>
  </div>
</template>
