<script setup>
import { inject, ref, computed } from 'vue'
import { analyzeRepo, uploadZip } from '../api.js'

const analysis = inject('analysis')
const repoPath = inject('repoPath')
const loading = inject('loading')
const error = inject('error')

const dragging = ref(false)
const uploadName = ref('')
const fileInput = ref(null)

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

async function handleFile(file) {
  if (!file) return
  if (!file.name.endsWith('.zip')) {
    error.value = 'Only .zip files are supported.'
    return
  }
  if (file.size > 50 * 1024 * 1024) {
    error.value = 'File too large. Maximum size is 50MB.'
    return
  }
  loading.value = true
  error.value = ''
  uploadName.value = file.name
  try {
    analysis.value = await uploadZip(file)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
    uploadName.value = ''
  }
}

function onDrop(e) {
  dragging.value = false
  const file = e.dataTransfer?.files?.[0]
  handleFile(file)
}

function onFileSelect(e) {
  const file = e.target?.files?.[0]
  handleFile(file)
  if (fileInput.value) fileInput.value.value = ''
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
        Enter a local path, GitHub URL, or drop a zip file.
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

      <!-- Divider -->
      <div class="flex items-center gap-4 w-full">
        <div class="flex-1 h-px bg-bg-inset"></div>
        <span class="text-[11px] text-text-muted font-mono tracking-wider">OR</span>
        <div class="flex-1 h-px bg-bg-inset"></div>
      </div>

      <!-- Drop zone -->
      <div
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="onDrop"
        @click="fileInput?.click()"
        :class="[
          'w-full border-2 border-dashed rounded-xl py-8 px-6 flex flex-col items-center gap-3 cursor-pointer transition-all duration-200',
          dragging
            ? 'border-accent bg-accent/5 scale-[1.01]'
            : 'border-bg-inset hover:border-text-muted/30 hover:bg-bg-surface/50',
        ]"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".zip"
          class="hidden"
          @change="onFileSelect"
        />
        <div v-if="loading && uploadName" class="flex flex-col items-center gap-2">
          <svg class="animate-spin w-6 h-6 text-accent" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span class="text-sm text-text-secondary font-mono">Analyzing {{ uploadName }}…</span>
        </div>
        <template v-else>
          <svg class="w-8 h-8 text-text-muted" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
          <div class="text-center">
            <span class="text-sm text-text-secondary">Drop a <span class="font-mono text-accent">.zip</span> file here or <span class="text-accent font-medium">browse</span></span>
            <p class="text-[11px] text-text-muted mt-1">Max 50 MB</p>
          </div>
        </template>
      </div>

      <p v-if="error" class="text-risk-high text-sm text-center">{{ error }}</p>
    </div>
  </div>
</template>
