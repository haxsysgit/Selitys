<script setup>
defineProps({ entryPoints: Array })
</script>

<template>
  <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-4">
    <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">ENTRY POINTS</span>
    <div
      v-for="ep in entryPoints"
      :key="ep.path"
      class="flex items-center gap-3"
    >
      <span class="font-mono text-xs text-accent">✓</span>
      <span class="font-mono text-sm text-text-primary">{{ ep.path }}</span>
      <span class="text-xs text-text-tertiary">{{ ep.description }}</span>
    </div>
    <p v-if="!entryPoints?.length" class="text-sm text-text-muted">No entry points detected.</p>
  </div>
</template>
