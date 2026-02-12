<script setup>
defineProps({ risks: Array })

const sevStyle = {
  high: { bg: 'bg-risk-high/15', text: 'text-risk-high', label: 'HIGH' },
  medium: { bg: 'bg-risk-medium/15', text: 'text-risk-medium', label: 'MED' },
  low: { bg: 'bg-text-tertiary/15', text: 'text-text-tertiary', label: 'LOW' },
}
</script>

<template>
  <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-3">
    <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">TOP RISKS</span>
    <div
      v-for="(risk, i) in risks?.slice(0, 6)"
      :key="i"
      class="flex items-center gap-2"
    >
      <span
        class="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0"
        :class="[sevStyle[risk.severity]?.bg, sevStyle[risk.severity]?.text]"
      >
        {{ sevStyle[risk.severity]?.label || risk.severity }}
      </span>
      <span class="text-xs truncate" :class="risk.severity === 'low' ? 'text-text-secondary' : 'text-text-primary'">
        {{ risk.risk_type }} in {{ risk.location }}
      </span>
    </div>
    <p v-if="!risks?.length" class="text-sm text-text-muted">No risks detected.</p>
  </div>
</template>
