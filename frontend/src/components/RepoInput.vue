<script setup>
import { inject, computed } from 'vue'
import { analyzeRepo } from '../api.js'

const analysis = inject('analysis')
const repoPath = inject('repoPath')
const loading = inject('loading')
const error = inject('error')

const isGitHub = computed(() =>
  /^https?:\/\/github\.com\/[\w.-]+\/[\w.-]+/.test(repoPath.value.trim())
)

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
        <img src="/logo.svg" alt="selitys" class="w-12 h-12" />
        <h1 class="text-3xl font-bold font-mono">selitys</h1>
      </div>
      <p class="text-text-secondary text-center text-sm leading-relaxed">
        Explain a backend codebase to a new developer.<br />
        Enter a local path or a GitHub URL to analyze.
      </p>
      <form @submit.prevent="handleAnalyze" class="flex flex-col w-full gap-3">
        <div class="flex w-full gap-3">
          <div class="flex-1 flex items-center bg-bg-surface rounded-lg focus-within:ring-1 focus-within:ring-accent transition-all duration-200">
            <input
              v-model="repoPath"
              type="text"
              placeholder="/path/to/repo or https://github.com/user/repo"
              class="flex-1 min-w-0 bg-transparent text-text-primary font-mono text-sm py-3 pl-4 pr-2 border-none outline-none placeholder:text-text-muted"
            />
            <span
              v-if="isGitHub"
              class="shrink-0 mr-3 text-[11px] font-mono font-bold text-accent bg-accent/10 px-2 py-0.5 rounded"
            >GitHub</span>
          </div>
          <button
            type="submit"
            :disabled="loading || !repoPath.trim()"
            class="bg-accent text-bg-primary font-semibold px-6 py-3 rounded-lg text-sm transition-all duration-200 hover:opacity-90 hover:scale-[1.02] disabled:opacity-40 disabled:hover:scale-100"
          >
            {{ loading ? (isGitHub ? 'Cloning...' : 'Analyzing...') : 'Analyze' }}
          </button>
        </div>
        <p v-if="isGitHub && !loading" class="text-xs text-text-tertiary text-center">
          Public repo will be cloned with <span class="font-mono text-accent">git clone --depth 1</span>
        </p>
      </form>
      <p v-if="error" class="text-risk-high text-sm text-center">{{ error }}</p>
    </div>
  </div>
</template>
