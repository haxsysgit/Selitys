<script setup>
import { inject, ref } from 'vue'
import Collapsible from '../components/Collapsible.vue'

const analysis = inject('analysis')
const expandedFile = ref(null)

function toggleFile(path) {
  expandedFile.value = expandedFile.value === path ? null : path
}

const stepLabels = [
  'Entry point first — understand how the application boots',
  'Configuration second — know what settings and env vars exist',
  'Data models third — understand the domain entities',
  'API routes fourth — see the public interface',
  'Services last — dive into business logic with context',
  'Documentation — high-level overview and setup',
]
</script>

<template>
  <div v-if="analysis" class="p-8 lg:px-10 flex flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-semibold">First Read Guide</h1>
      <p class="text-sm text-text-secondary">{{ analysis.repo_name }} — recommended reading order for new developers</p>
    </div>

    <!-- Reading order (interactive timeline) -->
    <Collapsible title="START HERE" :badge="analysis.first_read_files?.length" badge-color="bg-green-400/10 text-green-400">
      <div class="flex flex-col">
        <div
          v-for="(file, i) in analysis.first_read_files"
          :key="file.path"
          class="flex gap-4 cursor-pointer"
          @click="toggleFile(file.path)"
        >
          <!-- Number + connector -->
          <div class="flex flex-col items-center w-8 shrink-0">
            <div
              class="w-8 h-8 rounded-lg flex items-center justify-center font-mono text-sm font-bold shrink-0 transition-colors duration-200"
              :class="expandedFile === file.path ? 'bg-accent text-bg-primary' : 'bg-accent/15 text-accent'"
            >{{ i + 1 }}</div>
            <div
              v-if="i < analysis.first_read_files.length - 1"
              class="w-px flex-1 bg-accent/20 my-1"
            />
          </div>
          <!-- Content -->
          <div class="flex flex-col gap-1 pb-5 flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="font-mono text-sm font-semibold text-text-primary">{{ file.path }}</span>
              <span
                class="font-mono text-[11px] text-text-muted transition-transform duration-200"
                :class="expandedFile === file.path ? 'rotate-90' : ''"
              >▸</span>
            </div>
            <p class="text-sm text-text-secondary">{{ file.reason }}</p>
            <div v-if="expandedFile === file.path" class="mt-1 bg-bg-inset rounded-lg px-3 py-2">
              <span class="text-xs text-text-tertiary italic">{{ stepLabels[i] || 'Read to understand this part of the system' }}</span>
            </div>
          </div>
        </div>
      </div>
      <p v-if="!analysis.first_read_files?.length" class="text-sm text-text-muted">No reading order recommendations.</p>
    </Collapsible>

    <!-- Skip files (grouped by reason) -->
    <Collapsible
      v-if="analysis.skip_files?.length"
      title="SKIP THESE FOR NOW"
      :badge="analysis.skip_files.length"
      badge-color="bg-text-tertiary/15 text-text-tertiary"
      :default-open="false"
    >
      <div class="flex flex-col gap-1">
        <div
          v-for="file in analysis.skip_files"
          :key="file.path"
          class="flex items-center gap-3 py-1.5"
        >
          <span class="font-mono text-xs text-text-muted shrink-0">✕</span>
          <span class="font-mono text-xs text-text-tertiary truncate">{{ file.path }}</span>
          <span class="text-[11px] text-text-muted shrink-0">{{ file.reason }}</span>
        </div>
      </div>
    </Collapsible>
  </div>
</template>
