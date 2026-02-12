<script setup>
import { inject } from 'vue'

const analysis = inject('analysis')
</script>

<template>
  <div v-if="analysis" class="p-8 lg:px-10 flex flex-col gap-8">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-semibold">First Read Guide</h1>
      <p class="text-sm text-text-secondary">{{ analysis.repo_name }} — recommended reading order for new developers</p>
    </div>

    <!-- Start reading -->
    <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-4">
      <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">START HERE</span>
      <div
        v-for="(file, i) in analysis.first_read_files"
        :key="file.path"
        class="flex items-start gap-4 bg-bg-inset rounded-lg p-4"
      >
        <span class="font-mono text-lg font-bold text-accent shrink-0 w-8 text-center">{{ i + 1 }}</span>
        <div class="flex flex-col gap-1">
          <span class="font-mono text-sm font-semibold text-text-primary">{{ file.path }}</span>
          <p class="text-sm text-text-secondary">{{ file.reason }}</p>
        </div>
      </div>
      <p v-if="!analysis.first_read_files?.length" class="text-sm text-text-muted">No reading order recommendations.</p>
    </div>

    <!-- Skip these -->
    <div v-if="analysis.skip_files?.length" class="bg-bg-surface rounded-xl p-5 flex flex-col gap-4">
      <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">SKIP THESE (FOR NOW)</span>
      <div
        v-for="file in analysis.skip_files"
        :key="file.path"
        class="flex items-center gap-3"
      >
        <span class="font-mono text-xs text-text-muted">✕</span>
        <span class="font-mono text-sm text-text-tertiary">{{ file.path }}</span>
        <span class="text-xs text-text-muted">{{ file.reason }}</span>
      </div>
    </div>
  </div>
</template>
