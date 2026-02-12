<script setup>
import { ref } from 'vue'

const props = defineProps({
  title: String,
  subtitle: String,
  badge: [String, Number],
  badgeColor: { type: String, default: 'bg-accent/10 text-accent' },
  defaultOpen: { type: Boolean, default: true },
})

const open = ref(props.defaultOpen)
</script>

<template>
  <div class="bg-bg-surface rounded-xl overflow-hidden">
    <button
      @click="open = !open"
      class="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-bg-inset/30 transition-all duration-200 group"
    >
      <div class="flex items-center gap-3">
        <span
          class="font-mono text-xs text-text-muted transition-transform duration-200"
          :class="open ? 'rotate-90' : ''"
        >▸</span>
        <span class="text-[11px] font-semibold text-text-tertiary tracking-[2px]">{{ title }}</span>
        <span
          v-if="badge !== undefined"
          class="text-[11px] font-mono font-bold px-2 py-0.5 rounded-full"
          :class="badgeColor"
        >{{ badge }}</span>
      </div>
      <span v-if="subtitle" class="text-xs text-text-muted hidden sm:block">{{ subtitle }}</span>
    </button>
    <div v-show="open" class="px-5 pb-5">
      <slot />
    </div>
  </div>
</template>
