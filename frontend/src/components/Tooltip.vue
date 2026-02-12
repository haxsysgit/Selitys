<script setup>
defineProps({
  text: String,
  position: { type: String, default: 'top' },
})
</script>

<template>
  <div class="relative group inline-flex">
    <slot />
    <div
      :class="[
        'absolute z-50 px-2.5 py-1.5 text-xs rounded-lg bg-bg-surface text-text-primary border border-bg-inset whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-200',
        position === 'top' && 'bottom-full left-1/2 -translate-x-1/2 mb-2',
        position === 'bottom' && 'top-full left-1/2 -translate-x-1/2 mt-2',
        position === 'left' && 'right-full top-1/2 -translate-y-1/2 mr-2',
        position === 'right' && 'left-full top-1/2 -translate-y-1/2 ml-2',
      ]"
    >{{ text }}</div>
  </div>
</template>
