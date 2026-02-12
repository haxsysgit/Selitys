<script setup>
import { inject } from 'vue'

const analysis = inject('analysis')
</script>

<template>
  <div v-if="analysis" class="p-8 lg:px-10 flex flex-col gap-8">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-semibold">Architecture</h1>
      <p class="text-sm text-text-secondary">{{ analysis.repo_name }} — subsystems, patterns, and frameworks</p>
    </div>

    <!-- Patterns -->
    <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-3">
      <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">PATTERNS DETECTED</span>
      <div class="flex flex-wrap gap-2">
        <span
          v-for="p in analysis.patterns_detected"
          :key="p"
          class="text-sm text-accent bg-accent/10 px-3 py-1.5 rounded-lg"
        >{{ p }}</span>
      </div>
      <p v-if="!analysis.patterns_detected?.length" class="text-sm text-text-muted">No patterns detected.</p>
    </div>

    <!-- Frameworks -->
    <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-3">
      <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">FRAMEWORKS &amp; LIBRARIES</span>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div
          v-for="fw in analysis.frameworks"
          :key="fw.name"
          class="bg-bg-inset rounded-lg p-4 flex flex-col gap-1"
        >
          <span class="font-mono text-sm font-semibold text-text-primary">{{ fw.name }}</span>
          <span class="text-xs text-text-tertiary">{{ fw.category }}</span>
        </div>
      </div>
    </div>

    <!-- Subsystems -->
    <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-4">
      <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">SUBSYSTEMS</span>
      <div
        v-for="sub in analysis.subsystems"
        :key="sub.name"
        class="bg-bg-inset rounded-lg p-4 flex flex-col gap-2"
      >
        <div class="flex items-center gap-3">
          <span class="font-mono text-sm font-semibold text-text-primary">{{ sub.name }}</span>
          <span class="font-mono text-xs text-text-muted">{{ sub.directory }}</span>
        </div>
        <p class="text-sm text-text-secondary">{{ sub.description }}</p>
        <div v-if="sub.key_files?.length" class="flex flex-wrap gap-2 mt-1">
          <span
            v-for="f in sub.key_files"
            :key="f"
            class="font-mono text-[11px] text-text-tertiary bg-bg-surface px-2 py-0.5 rounded"
          >{{ f }}</span>
        </div>
      </div>
      <p v-if="!analysis.subsystems?.length" class="text-sm text-text-muted">No subsystems detected.</p>
    </div>

    <!-- Languages breakdown -->
    <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-3">
      <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">LANGUAGES</span>
      <div class="flex flex-col gap-2">
        <div
          v-for="(lines, lang) in analysis.languages"
          :key="lang"
          class="flex items-center gap-3"
        >
          <span class="font-mono text-sm text-text-primary w-28">{{ lang }}</span>
          <div class="flex-1 h-2 bg-bg-inset rounded-full overflow-hidden">
            <div
              class="h-full bg-accent rounded-full"
              :style="{ width: Math.max(2, (lines / analysis.total_lines) * 100) + '%' }"
            />
          </div>
          <span class="font-mono text-xs text-text-tertiary w-20 text-right">{{ lines.toLocaleString() }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
