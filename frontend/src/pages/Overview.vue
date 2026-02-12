<script setup>
import { inject } from 'vue'
import MetricCards from '../components/MetricCards.vue'
import Collapsible from '../components/Collapsible.vue'

const analysis = inject('analysis')

function changeRepo() {
  analysis.value = null
}

const methodColor = {
  GET: 'bg-accent/10 text-accent',
  POST: 'bg-green-400/10 text-green-400',
  PUT: 'bg-yellow-400/10 text-yellow-400',
  PATCH: 'bg-orange-400/10 text-orange-400',
  DELETE: 'bg-risk-high/10 text-risk-high',
}

const sevStyle = {
  high: { cls: 'bg-risk-high/15 text-risk-high', label: 'HIGH' },
  medium: { cls: 'bg-risk-medium/15 text-risk-medium', label: 'MED' },
  low: { cls: 'bg-text-tertiary/15 text-text-tertiary', label: 'LOW' },
}
</script>

<template>
  <div v-if="analysis" class="p-8 lg:px-10 flex flex-col gap-6">
    <!-- Header -->
    <div class="flex items-start justify-between">
      <div class="flex flex-col gap-1">
        <h1 class="text-2xl font-semibold">{{ analysis.repo_name }}</h1>
        <p class="font-mono text-xs text-text-tertiary">
          {{ Object.keys(analysis.languages).join(' · ') }}
          · {{ analysis.total_files }} files
          · {{ analysis.total_lines.toLocaleString() }} lines
        </p>
        <p class="text-sm text-text-secondary mt-1">{{ analysis.likely_purpose }}</p>
      </div>
      <button
        @click="changeRepo"
        class="px-4 py-2 rounded-md bg-bg-surface text-text-secondary text-sm hover:text-text-primary transition-colors shrink-0"
      >Change Repo</button>
    </div>

    <!-- Metric Cards -->
    <MetricCards :analysis="analysis" />

    <!-- Two-column layout -->
    <div class="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
      <div class="flex flex-col gap-6">
        <!-- Entry Points -->
        <Collapsible title="ENTRY POINTS" :badge="analysis.entry_points?.length">
          <div class="flex flex-col gap-2">
            <div
              v-for="ep in analysis.entry_points"
              :key="ep.path"
              class="flex items-center gap-3"
            >
              <span class="font-mono text-xs text-accent">▶</span>
              <span class="font-mono text-sm text-text-primary">{{ ep.path }}</span>
              <span class="text-xs text-text-tertiary">{{ ep.description }}</span>
            </div>
            <p v-if="!analysis.entry_points?.length" class="text-sm text-text-muted">None detected.</p>
          </div>
        </Collapsible>

        <!-- API Surface -->
        <Collapsible title="API SURFACE" :badge="analysis.api_endpoints?.length" badge-color="bg-green-400/10 text-green-400">
          <div class="flex flex-col gap-2">
            <div
              v-for="(ep, i) in analysis.api_endpoints"
              :key="i"
              class="flex items-center gap-2"
            >
              <span
                class="font-mono text-[11px] font-bold px-2 py-0.5 rounded shrink-0"
                :class="methodColor[ep.method] || 'bg-bg-inset text-text-secondary'"
              >{{ ep.method }}</span>
              <span class="font-mono text-sm text-text-primary">{{ ep.path }}</span>
              <span class="text-xs text-text-muted truncate">{{ ep.description }}</span>
            </div>
            <p v-if="!analysis.api_endpoints?.length" class="text-sm text-text-muted">None detected.</p>
          </div>
        </Collapsible>
      </div>

      <div class="flex flex-col gap-6">
        <!-- Domain Entities -->
        <Collapsible title="DOMAIN ENTITIES" :badge="analysis.domain_entities?.length">
          <div class="flex flex-wrap gap-2">
            <span
              v-for="entity in analysis.domain_entities"
              :key="entity"
              class="font-mono text-xs text-accent bg-accent/10 px-3 py-1 rounded-full"
            >{{ entity.split(' (')[0] }}</span>
          </div>
          <p v-if="!analysis.domain_entities?.length" class="text-sm text-text-muted">None detected.</p>
        </Collapsible>

        <!-- Risks -->
        <Collapsible
          title="RISKS"
          :badge="analysis.risk_areas?.length"
          :badge-color="analysis.risk_areas?.some(r => r.severity === 'high') ? 'bg-risk-high/15 text-risk-high' : 'bg-risk-medium/15 text-risk-medium'"
        >
          <div class="flex flex-col gap-2">
            <div
              v-for="(risk, i) in analysis.risk_areas"
              :key="i"
              class="flex items-start gap-2"
            >
              <span
                class="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0 mt-0.5"
                :class="sevStyle[risk.severity]?.cls"
              >{{ sevStyle[risk.severity]?.label || risk.severity }}</span>
              <div class="flex flex-col">
                <span class="text-xs text-text-primary">{{ risk.risk_type }}</span>
                <span class="text-xs text-text-muted">{{ risk.location }}</span>
              </div>
            </div>
            <p v-if="!analysis.risk_areas?.length" class="text-sm text-text-muted">No risks detected.</p>
          </div>
        </Collapsible>

        <!-- Patterns -->
        <Collapsible title="PATTERNS" :badge="analysis.patterns_detected?.length" :default-open="false">
          <div class="flex flex-wrap gap-2">
            <span
              v-for="p in analysis.patterns_detected"
              :key="p"
              class="text-xs text-accent bg-accent/10 px-3 py-1.5 rounded-lg"
            >{{ p }}</span>
          </div>
          <p v-if="!analysis.patterns_detected?.length" class="text-sm text-text-muted">None detected.</p>
        </Collapsible>
      </div>
    </div>
  </div>
</template>
