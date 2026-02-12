<script setup>
import { inject, ref } from 'vue'
import Collapsible from '../components/Collapsible.vue'

const analysis = inject('analysis')
const expandedStep = ref(null)

function toggleStep(order) {
  expandedStep.value = expandedStep.value === order ? null : order
}
</script>

<template>
  <div v-if="analysis" class="p-8 lg:px-10 flex flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-semibold">Request Flow</h1>
      <p class="text-sm text-text-secondary">{{ analysis.repo_name }} — how a request moves through the system</p>
    </div>

    <template v-if="analysis.request_flow">
      <!-- Flow info -->
      <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-2">
        <span class="font-mono text-lg font-semibold text-text-primary">{{ analysis.request_flow.name }}</span>
        <p class="text-sm text-text-secondary leading-relaxed">{{ analysis.request_flow.description }}</p>
      </div>

      <!-- Steps (interactive timeline) -->
      <Collapsible title="FLOW STEPS" :badge="analysis.request_flow.steps?.length">
        <div class="flex flex-col">
          <div
            v-for="step in analysis.request_flow.steps"
            :key="step.order"
            class="flex gap-4 relative cursor-pointer"
            @click="toggleStep(step.order)"
          >
            <!-- Vertical line + dot -->
            <div class="flex flex-col items-center w-6 shrink-0">
              <div
                class="w-3.5 h-3.5 rounded-full shrink-0 mt-1.5 transition-colors duration-200"
                :class="expandedStep === step.order ? 'bg-accent' : 'bg-accent/40'"
              />
              <div
                v-if="step.order < analysis.request_flow.steps.length"
                class="w-px flex-1 bg-accent/20 my-1"
              />
            </div>
            <!-- Content -->
            <div class="flex flex-col gap-1 pb-5 flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="font-mono text-xs font-bold text-accent">{{ step.order }}</span>
                <span class="font-mono text-sm font-semibold text-text-primary">{{ step.location }}</span>
                <span
                  class="font-mono text-[11px] text-text-muted transition-transform duration-200"
                  :class="expandedStep === step.order ? 'rotate-90' : ''"
                >▸</span>
              </div>
              <p
                class="text-sm transition-colors"
                :class="expandedStep === step.order ? 'text-text-primary' : 'text-text-secondary'"
              >{{ step.description }}</p>
              <div v-if="expandedStep === step.order && step.file_path" class="mt-1 bg-bg-inset rounded-lg px-3 py-2">
                <span class="font-mono text-xs text-accent">{{ step.file_path }}</span>
              </div>
            </div>
          </div>
        </div>
      </Collapsible>

      <!-- Touchpoints -->
      <Collapsible
        v-if="analysis.request_flow.touchpoints?.length"
        title="TOUCHPOINTS"
        :badge="analysis.request_flow.touchpoints.length"
        :default-open="false"
      >
        <div class="flex flex-wrap gap-2">
          <span
            v-for="tp in analysis.request_flow.touchpoints"
            :key="tp"
            class="font-mono text-xs text-text-secondary bg-bg-inset px-3 py-1.5 rounded-lg"
          >{{ tp }}</span>
        </div>
      </Collapsible>
    </template>

    <div v-else class="bg-bg-surface rounded-xl p-8 flex items-center justify-center">
      <p class="text-text-muted text-sm">No request flow detected for this codebase.</p>
    </div>
  </div>
</template>
