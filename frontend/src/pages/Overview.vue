<script setup>
import { inject } from 'vue'
import MetricCards from '../components/MetricCards.vue'
import EntryPoints from '../components/EntryPoints.vue'
import DomainEntities from '../components/DomainEntities.vue'
import RiskSummary from '../components/RiskSummary.vue'
import ApiSurface from '../components/ApiSurface.vue'

const analysis = inject('analysis')
const repoPath = inject('repoPath')

const loading = inject('loading')

function changeRepo() {
  analysis.value = null
}
</script>

<template>
  <div v-if="analysis" class="p-8 lg:px-10 flex flex-col gap-8">
    <!-- Header -->
    <div class="flex items-start justify-between">
      <div class="flex flex-col gap-1">
        <h1 class="text-2xl font-semibold">{{ analysis.repo_name }}</h1>
        <p class="font-mono text-xs text-text-tertiary">
          {{ Object.keys(analysis.languages).join(' · ') }}
          · {{ analysis.total_files }} files
          · {{ analysis.total_lines.toLocaleString() }} lines
        </p>
      </div>
      <div class="flex gap-3">
        <button
          @click="changeRepo"
          class="px-4 py-2 rounded-md bg-bg-surface text-text-secondary text-sm hover:text-text-primary transition-colors"
        >
          Change Repo
        </button>
      </div>
    </div>

    <!-- Metric Cards -->
    <MetricCards :analysis="analysis" />

    <!-- Two-column layout -->
    <div class="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
      <div class="flex flex-col gap-6">
        <EntryPoints :entry-points="analysis.entry_points" />
        <ApiSurface :endpoints="analysis.api_endpoints" />
      </div>
      <div class="flex flex-col gap-6">
        <DomainEntities :entities="analysis.domain_entities" />
        <RiskSummary :risks="analysis.risk_areas" />
      </div>
    </div>
  </div>
</template>
