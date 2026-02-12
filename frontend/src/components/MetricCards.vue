<script setup>
import { computed } from 'vue'

const props = defineProps({ analysis: Object })

const cards = computed(() => [
  {
    label: 'PURPOSE',
    value: props.analysis.likely_purpose.replace(/^This appears to be /, '').split('.')[0],
    color: 'text-text-primary',
  },
  {
    label: 'LANGUAGES',
    value: String(Object.keys(props.analysis.languages).length),
    sub: Object.keys(props.analysis.languages).slice(0, 4).join(', '),
    color: 'text-accent',
  },
  {
    label: 'FRAMEWORKS',
    value: String(props.analysis.frameworks.length),
    sub: props.analysis.frameworks.map(f => f.name).slice(0, 3).join(', '),
    color: 'text-accent',
  },
  {
    label: 'RISKS',
    value: String(props.analysis.risk_areas.length),
    sub: [
      props.analysis.risk_areas.filter(r => r.severity === 'high').length + ' high',
      props.analysis.risk_areas.filter(r => r.severity === 'medium').length + ' medium',
      props.analysis.risk_areas.filter(r => r.severity === 'low').length + ' low',
    ].join(', '),
    color: props.analysis.risk_areas.some(r => r.severity === 'high') ? 'text-risk-high' : 'text-accent',
  },
])
</script>

<template>
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
    <div
      v-for="card in cards"
      :key="card.label"
      class="bg-bg-surface rounded-xl p-5 flex flex-col gap-2 transition-all duration-200 hover:scale-[1.02] hover:ring-1 hover:ring-accent/20 cursor-default"
    >
      <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">{{ card.label }}</span>
      <span class="font-mono text-xl font-bold" :class="card.color">{{ card.value }}</span>
      <span v-if="card.sub" class="text-xs text-text-secondary">{{ card.sub }}</span>
    </div>
  </div>
</template>
