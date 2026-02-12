<script setup>
import { ref, inject, nextTick } from 'vue'
import { askQuestion } from '../api.js'

const analysis = inject('analysis')
const repoPath = inject('repoPath')

const question = ref('')
const useLlm = ref(true)
const messages = ref([])
const asking = ref(false)
const chatArea = ref(null)

async function handleAsk() {
  const q = question.value.trim()
  if (!q || asking.value) return

  messages.value.push({ role: 'user', content: q })
  question.value = ''
  asking.value = true

  await nextTick()
  scrollToBottom()

  try {
    const res = await askQuestion(repoPath.value, q, { useLlm: useLlm.value })
    if (res.mode === 'llm') {
      messages.value.push({ role: 'assistant', content: res.answer })
    } else {
      messages.value.push({
        role: 'assistant',
        content: res.summary,
        details: res.details,
        files: res.related_files,
        confidence: res.confidence,
      })
    }
  } catch (e) {
    messages.value.push({ role: 'error', content: e.message })
  } finally {
    asking.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (chatArea.value) {
    chatArea.value.scrollTop = chatArea.value.scrollHeight
  }
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="flex items-start justify-between px-8 lg:px-10 pt-8 pb-4">
      <div class="flex flex-col gap-1">
        <h1 class="text-2xl font-semibold">Ask about {{ analysis?.repo_name }}</h1>
        <p class="font-mono text-xs text-text-tertiary">
          {{ useLlm ? 'Powered by LLM' : 'Keyword-based' }}
        </p>
      </div>
      <div class="flex items-center bg-bg-surface rounded-lg p-1 gap-1">
        <button
          @click="useLlm = false"
          :class="[
            'px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
            !useLlm ? 'bg-accent text-bg-primary' : 'text-text-tertiary hover:text-text-secondary'
          ]"
        >Keyword</button>
        <button
          @click="useLlm = true"
          :class="[
            'px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
            useLlm ? 'bg-accent text-bg-primary' : 'text-text-tertiary hover:text-text-secondary'
          ]"
        >LLM</button>
      </div>
    </div>

    <!-- Chat area -->
    <div ref="chatArea" class="flex-1 overflow-y-auto px-8 lg:px-10 py-4 flex flex-col gap-5">
      <div v-if="!messages.length" class="flex-1 flex items-center justify-center">
        <p class="text-text-muted text-sm">Ask anything about this codebase...</p>
      </div>

      <template v-for="(msg, i) in messages" :key="i">
        <!-- User message -->
        <div v-if="msg.role === 'user'" class="flex justify-end">
          <div class="bg-bg-surface px-4 py-2.5 rounded-xl rounded-br-sm max-w-[70%]">
            <p class="text-sm">{{ msg.content }}</p>
          </div>
        </div>

        <!-- Assistant message -->
        <div v-else-if="msg.role === 'assistant'" class="flex flex-col gap-3 bg-bg-inset rounded-xl p-5 max-w-[85%]">
          <div class="flex items-center gap-2">
            <div class="w-5 h-5 rounded bg-accent" />
            <span class="font-mono text-xs font-semibold text-accent">selitys</span>
          </div>
          <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ msg.content }}</p>
          <ul v-if="msg.details?.length" class="flex flex-col gap-1.5 mt-1">
            <li v-for="d in msg.details" :key="d" class="text-sm text-text-secondary">• {{ d }}</li>
          </ul>
          <div v-if="msg.files?.length" class="flex flex-wrap gap-2 mt-1">
            <span
              v-for="f in msg.files.slice(0, 6)"
              :key="f"
              class="font-mono text-[11px] text-text-tertiary bg-bg-surface px-2 py-1 rounded"
            >{{ f }}</span>
          </div>
        </div>

        <!-- Error -->
        <div v-else-if="msg.role === 'error'" class="bg-risk-high/10 text-risk-high text-sm px-4 py-3 rounded-xl max-w-[85%]">
          {{ msg.content }}
        </div>
      </template>

      <div v-if="asking" class="flex items-center gap-2 text-text-muted text-sm">
        <span class="animate-pulse">●</span> Thinking...
      </div>
    </div>

    <!-- Input bar -->
    <form @submit.prevent="handleAsk" class="flex items-center gap-3 px-8 lg:px-10 pb-8 pt-4">
      <input
        v-model="question"
        type="text"
        placeholder="Ask anything about this codebase..."
        class="flex-1 bg-bg-surface text-text-primary font-sans text-sm px-4 py-3 rounded-lg border-none outline-none placeholder:text-text-muted focus:ring-1 focus:ring-accent"
        :disabled="asking"
      />
      <button
        type="submit"
        :disabled="asking || !question.trim()"
        class="bg-accent text-bg-primary font-mono font-bold text-lg px-4 py-2.5 rounded-lg transition-opacity hover:opacity-90 disabled:opacity-40"
      >→</button>
    </form>
  </div>
</template>
