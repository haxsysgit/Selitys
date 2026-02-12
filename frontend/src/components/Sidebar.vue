<script setup>
import { useRoute } from 'vue-router'
import { useTheme } from '../useTheme.js'

defineProps({ hasAnalysis: Boolean })
const route = useRoute()
const { theme, toggle } = useTheme()

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
  <aside class="w-60 shrink-0 bg-bg-inset flex flex-col px-4 py-6 gap-2 transition-colors duration-300">
    <router-link to="/" class="group flex items-center gap-2 pb-6 no-underline">
      <img src="/logo.svg" alt="selitys" class="w-8 h-8 transition-transform duration-200 group-hover:scale-110" />
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
          'group flex items-center gap-2 px-3 py-2 rounded-md text-sm no-underline transition-all duration-200',
          route.name === item.name
            ? 'bg-bg-surface text-text-primary translate-x-1'
            : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface/50 hover:translate-x-1',
          !hasAnalysis && 'opacity-40 pointer-events-none'
        ]"
      >
        <span
          class="font-mono text-sm transition-colors duration-200"
          :class="route.name === item.name ? 'text-accent' : 'text-text-tertiary group-hover:text-accent'"
        >{{ item.icon }}</span>
        {{ item.label }}
      </router-link>
    </template>

    <!-- Theme toggle at bottom -->
    <div class="mt-auto pt-4 border-t border-bg-surface/50">
      <button
        @click="toggle"
        class="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm text-text-secondary hover:text-text-primary hover:bg-bg-surface/50 transition-all duration-200"
        :title="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
      >
        <span class="font-mono text-sm text-text-tertiary">{{ theme === 'dark' ? '☀' : '☾' }}</span>
        {{ theme === 'dark' ? 'Light Mode' : 'Dark Mode' }}
      </button>
    </div>
  </aside>
</template>
