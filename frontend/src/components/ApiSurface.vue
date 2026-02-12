<script setup>
defineProps({ endpoints: Array })

const methodColor = {
  GET: { bg: 'bg-accent/10', text: 'text-accent' },
  POST: { bg: 'bg-green-400/10', text: 'text-green-400' },
  PUT: { bg: 'bg-yellow-400/10', text: 'text-yellow-400' },
  PATCH: { bg: 'bg-orange-400/10', text: 'text-orange-400' },
  DELETE: { bg: 'bg-risk-high/10', text: 'text-risk-high' },
}
</script>

<template>
  <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-4">
    <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">API SURFACE</span>
    <div
      v-for="(ep, i) in endpoints?.slice(0, 12)"
      :key="i"
      class="flex items-center gap-2"
    >
      <span
        class="font-mono text-[11px] font-bold px-2 py-0.5 rounded"
        :class="[methodColor[ep.method]?.bg || 'bg-bg-inset', methodColor[ep.method]?.text || 'text-text-secondary']"
      >
        {{ ep.method }}
      </span>
      <span class="font-mono text-sm text-text-primary">{{ ep.path }}</span>
    </div>
    <p v-if="endpoints?.length > 12" class="text-xs text-text-muted">
      +{{ endpoints.length - 12 }} more endpoints
    </p>
    <p v-if="!endpoints?.length" class="text-sm text-text-muted">No API endpoints detected.</p>
  </div>
</template>
