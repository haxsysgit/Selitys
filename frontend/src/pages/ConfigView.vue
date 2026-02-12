<script setup>
import { inject } from 'vue'

const analysis = inject('analysis')
</script>

<template>
  <div v-if="analysis" class="p-8 lg:px-10 flex flex-col gap-8">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-semibold">Configuration</h1>
      <p class="text-sm text-text-secondary">{{ analysis.repo_name }} — config files and environment variables</p>
    </div>

    <!-- Config files -->
    <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-3">
      <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">CONFIG FILES</span>
      <div
        v-for="cf in analysis.config_files"
        :key="cf"
        class="flex items-center gap-3 bg-bg-inset rounded-lg px-4 py-3"
      >
        <span class="font-mono text-xs text-accent">⚙</span>
        <span class="font-mono text-sm text-text-primary">{{ cf }}</span>
      </div>
      <p v-if="!analysis.config_files?.length" class="text-sm text-text-muted">No config files detected.</p>
    </div>

    <!-- Environment variables -->
    <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-3">
      <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">ENVIRONMENT VARIABLES</span>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <div
          v-for="ev in analysis.env_vars"
          :key="ev"
          class="font-mono text-sm text-text-secondary bg-bg-inset rounded-lg px-4 py-2.5"
        >{{ ev }}</div>
      </div>
      <p v-if="!analysis.env_vars?.length" class="text-sm text-text-muted">No environment variables detected.</p>
    </div>

    <!-- Entry Points -->
    <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-3">
      <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">ENTRY POINTS</span>
      <div
        v-for="ep in analysis.entry_points"
        :key="ep.path"
        class="flex items-center gap-3"
      >
        <span class="font-mono text-xs text-accent">▶</span>
        <span class="font-mono text-sm text-text-primary">{{ ep.path }}</span>
        <span class="text-xs text-text-tertiary">{{ ep.description }}</span>
      </div>
      <p v-if="!analysis.entry_points?.length" class="text-sm text-text-muted">No entry points detected.</p>
    </div>
  </div>
</template>
