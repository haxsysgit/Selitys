<script setup>
import { inject } from 'vue'
import { analyzeRepo } from '../api.js'

const analysis = inject('analysis')
const repoPath = inject('repoPath')
const loading = inject('loading')
const error = inject('error')

async function handleAnalyze() {
  if (!repoPath.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    analysis.value = await analyzeRepo(repoPath.value.trim())
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-center h-full">
    <div class="flex flex-col items-center gap-8 max-w-lg w-full px-8">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-accent" />
        <h1 class="text-3xl font-bold font-mono">selitys</h1>
      </div>
      <p class="text-text-secondary text-center text-sm leading-relaxed">
        Explain a backend codebase to a new developer.<br />
        Enter a repository path to analyze.
      </p>
      <form @submit.prevent="handleAnalyze" class="flex w-full gap-3">
        <input
          v-model="repoPath"
          type="text"
          placeholder="/path/to/your/repo"
          class="flex-1 bg-bg-surface text-text-primary font-mono text-sm px-4 py-3 rounded-lg border-none outline-none placeholder:text-text-muted focus:ring-1 focus:ring-accent"
        />
        <button
          type="submit"
          :disabled="loading || !repoPath.trim()"
          class="bg-accent text-bg-primary font-semibold px-6 py-3 rounded-lg text-sm transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          {{ loading ? 'Analyzing...' : 'Analyze' }}
        </button>
      </form>
      <p v-if="error" class="text-risk-high text-sm">{{ error }}</p>
    </div>
  </div>
</template>
