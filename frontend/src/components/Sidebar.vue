<script setup>
import { useRoute } from 'vue-router'

defineProps({ hasAnalysis: Boolean })
const route = useRoute()

const navItems = [
  { label: 'ANALYSIS', items: [
    { name: 'overview', icon: '◎', label: 'Overview', to: '/' },
    { name: 'architecture', icon: '△', label: 'Architecture', to: '/architecture' },
    { name: 'request-flow', icon: '→', label: 'Request Flow', to: '/request-flow' },
    { name: 'first-read', icon: '☰', label: 'First Read', to: '/first-read' },
    { name: 'config', icon: '⚙', label: 'Config', to: '/config' },
  ]},
  { label: 'INTERACT', items: [
    { name: 'ask', icon: '?', label: 'Ask', to: '/ask' },
  ]},
]
</script>

<template>
  <aside class="w-60 shrink-0 bg-bg-inset flex flex-col px-4 py-6 gap-2">
    <router-link to="/" class="flex items-center gap-2 pb-6 no-underline">
      <div class="w-7 h-7 rounded-md bg-accent" />
      <span class="font-mono text-lg font-bold text-text-primary">selitys</span>
    </router-link>

    <template v-for="section in navItems" :key="section.label">
      <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px] mt-2 mb-1">
        {{ section.label }}
      </span>
      <router-link
        v-for="item in section.items"
        :key="item.name"
        :to="hasAnalysis ? item.to : '#'"
        :class="[
          'flex items-center gap-2 px-3 py-2 rounded-md text-sm no-underline transition-colors',
          route.name === item.name
            ? 'bg-bg-surface text-text-primary'
            : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface/50',
          !hasAnalysis && 'opacity-40 pointer-events-none'
        ]"
      >
        <span class="font-mono text-sm" :class="route.name === item.name ? 'text-accent' : 'text-text-tertiary'">
          {{ item.icon }}
        </span>
        {{ item.label }}
      </router-link>
    </template>
  </aside>
</template>
