<script setup>
import { inject } from 'vue'

const analysis = inject('analysis')
</script>

<template>
  <div v-if="analysis" class="p-8 lg:px-10 flex flex-col gap-8">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-semibold">Request Flow</h1>
      <p class="text-sm text-text-secondary">{{ analysis.repo_name }} — how a request moves through the system</p>
    </div>

    <template v-if="analysis.request_flow">
      <!-- Flow info -->
      <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-3">
        <span class="font-mono text-lg font-semibold text-text-primary">{{ analysis.request_flow.name }}</span>
        <p class="text-sm text-text-secondary">{{ analysis.request_flow.description }}</p>
      </div>

      <!-- Steps -->
      <div class="bg-bg-surface rounded-xl p-5 flex flex-col gap-1">
        <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px] mb-3">FLOW STEPS</span>
        <div
          v-for="step in analysis.request_flow.steps"
          :key="step.order"
          class="flex gap-4 relative"
        >
          <!-- Vertical line + dot -->
          <div class="flex flex-col items-center w-6 shrink-0">
            <div class="w-3 h-3 rounded-full bg-accent shrink-0 mt-1.5" />
            <div
              v-if="step.order < analysis.request_flow.steps.length"
              class="w-px flex-1 bg-accent/20 my-1"
            />
          </div>
          <!-- Content -->
          <div class="flex flex-col gap-1 pb-5">
            <div class="flex items-center gap-2">
              <span class="font-mono text-xs text-accent">{{ step.order }}</span>
              <span class="font-mono text-sm font-semibold text-text-primary">{{ step.location }}</span>
            </div>
            <p class="text-sm text-text-secondary">{{ step.description }}</p>
            <span v-if="step.file_path" class="font-mono text-[11px] text-text-muted">{{ step.file_path }}</span>
          </div>
        </div>
      </div>

      <!-- Touchpoints -->
      <div v-if="analysis.request_flow.touchpoints?.length" class="bg-bg-surface rounded-xl p-5 flex flex-col gap-3">
        <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">TOUCHPOINTS</span>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="tp in analysis.request_flow.touchpoints"
            :key="tp"
            class="font-mono text-xs text-text-secondary bg-bg-inset px-3 py-1.5 rounded-lg"
          >{{ tp }}</span>
        </div>
      </div>
    </template>

    <div v-else class="bg-bg-surface rounded-xl p-8 flex items-center justify-center">
      <p class="text-text-muted text-sm">No request flow detected for this codebase.</p>
    </div>
  </div>
</template>
