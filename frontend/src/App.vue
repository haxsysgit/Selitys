<script setup>
import Sidebar from './components/Sidebar.vue'
import RepoInput from './components/RepoInput.vue'
import { ref, provide } from 'vue'

const analysis = ref(null)
const repoPath = ref('')
const loading = ref(false)
const error = ref('')

provide('analysis', analysis)
provide('repoPath', repoPath)
provide('loading', loading)
provide('error', error)
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <Sidebar :has-analysis="!!analysis" />
    <main class="flex-1 overflow-y-auto">
      <RepoInput v-if="!analysis" />
      <router-view v-else />
    </main>
  </div>
</template>
