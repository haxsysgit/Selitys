<script setup>
import { inject, ref } from 'vue'
import Collapsible from '../components/Collapsible.vue'

const analysis = inject('analysis')
const expandedSubs = ref(new Set())

function toggleSub(name) {
  if (expandedSubs.value.has(name)) {
    expandedSubs.value.delete(name)
  } else {
    expandedSubs.value.add(name)
  }
}
</script>

<template>
  <div v-if="analysis" class="p-8 lg:px-10 flex flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-semibold">Architecture</h1>
      <p class="text-sm text-text-secondary">{{ analysis.repo_name }} — subsystems, patterns, and frameworks</p>
    </div>

    <!-- Patterns -->
    <Collapsible title="PATTERNS" :badge="analysis.patterns_detected?.length">
      <div class="flex flex-wrap gap-2">
        <span
          v-for="p in analysis.patterns_detected"
          :key="p"
          class="text-sm text-accent bg-accent/10 px-3 py-1.5 rounded-lg"
        >{{ p }}</span>
      </div>
      <p v-if="!analysis.patterns_detected?.length" class="text-sm text-text-muted">No patterns detected.</p>
    </Collapsible>

    <!-- Frameworks -->
    <Collapsible title="FRAMEWORKS &amp; LIBRARIES" :badge="analysis.frameworks?.length">
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
    </Collapsible>

    <!-- Subsystems (tree hierarchy with expandable file lists) -->
    <Collapsible title="SUBSYSTEMS" :badge="analysis.subsystems?.length">
      <div class="flex flex-col gap-1">
        <div
          v-for="(sub, idx) in analysis.subsystems"
          :key="sub.name"
          class="flex flex-col"
        >
          <!-- Subsystem row (clickable) -->
          <button
            @click="toggleSub(sub.name)"
            class="flex items-start gap-2 px-3 py-2.5 rounded-lg text-left hover:bg-bg-inset/50 transition-colors w-full"
          >
            <span
              class="font-mono text-xs text-text-muted mt-1 transition-transform duration-200"
              :class="expandedSubs.has(sub.name) ? 'rotate-90' : ''"
            >▸</span>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="font-mono text-sm font-semibold text-text-primary">{{ sub.name }}</span>
                <span class="font-mono text-[11px] text-text-muted">{{ sub.directory }}</span>
                <span
                  v-if="sub.key_files?.length"
                  class="font-mono text-[10px] text-text-tertiary bg-bg-inset px-1.5 py-0.5 rounded"
                >{{ sub.key_files.length }} files</span>
              </div>
              <p class="text-xs text-text-secondary mt-0.5">{{ sub.description }}</p>
            </div>
          </button>

          <!-- Expanded file tree -->
          <div v-if="expandedSubs.has(sub.name) && sub.key_files?.length" class="ml-7 mb-2 flex flex-col">
            <div
              v-for="(f, fi) in sub.key_files"
              :key="f"
              class="flex items-center gap-2 py-1 pl-3 border-l border-bg-surface"
            >
              <span class="font-mono text-[11px] text-text-muted">{{ fi === sub.key_files.length - 1 ? '└' : '├' }}</span>
              <span class="font-mono text-xs text-text-tertiary">{{ f }}</span>
            </div>
          </div>
        </div>
        <p v-if="!analysis.subsystems?.length" class="text-sm text-text-muted">No subsystems detected.</p>
      </div>
    </Collapsible>

    <!-- Languages breakdown -->
    <Collapsible title="LANGUAGES" :badge="Object.keys(analysis.languages).length">
      <div class="flex flex-col gap-3">
        <div
          v-for="(lines, lang) in analysis.languages"
          :key="lang"
          class="flex items-center gap-3"
        >
          <span class="font-mono text-sm text-text-primary w-28">{{ lang }}</span>
          <div class="flex-1 h-2 bg-bg-inset rounded-full overflow-hidden">
            <div
              class="h-full bg-accent rounded-full transition-all duration-500"
              :style="{ width: Math.max(2, (lines / analysis.total_lines) * 100) + '%' }"
            />
          </div>
          <span class="font-mono text-xs text-text-tertiary w-20 text-right">{{ lines.toLocaleString() }}</span>
        </div>
      </div>
    </Collapsible>
  </div>
</template>
