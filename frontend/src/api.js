const BASE = ''

export async function analyzeRepo(repoPath) {
  const res = await fetch(`${BASE}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_path: repoPath }),
  })
  if (!res.ok) throw new Error((await res.json()).detail || res.statusText)
  return res.json()
}

export async function askQuestion(repoPath, question, { useLlm = false, apiKey, baseUrl, model } = {}) {
  const res = await fetch(`${BASE}/api/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repo_path: repoPath,
      question,
      use_llm: useLlm,
      api_key: apiKey || undefined,
      base_url: baseUrl || undefined,
      model: model || undefined,
    }),
  })
  if (!res.ok) throw new Error((await res.json()).detail || res.statusText)
  return res.json()
}

export async function uploadZip(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/api/upload`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error((await res.json()).detail || res.statusText)
  return res.json()
}

export async function healthCheck() {
  const res = await fetch(`${BASE}/api/health`)
  return res.json()
}
