<script setup>
import { inject, ref, computed, onMounted, nextTick, watch } from 'vue'

const analysis = inject('analysis')
const selected = ref(null)
const graphEl = ref(null)

const graph = computed(() => analysis.value?.dependency_graph || { nodes: [], edges: [], layers: [] })

const nodeMap = computed(() => {
  const m = {}
  for (const n of graph.value.nodes) m[n.path] = n
  return m
})

// Layout constants
const NODE_W = 150
const NODE_H = 36
const LAYER_GAP = 90
const NODE_GAP = 16
const PAD_X = 40
const PAD_TOP = 60

// Colors per type
const typeStyle = {
  entry_point: { fill: '#22c55e', bg: 'rgba(34,197,94,0.12)', text: '#22c55e', border: 'rgba(34,197,94,0.35)' },
  route:       { fill: '#22d3ee', bg: 'rgba(34,211,238,0.12)', text: '#22d3ee', border: 'rgba(34,211,238,0.35)' },
  service:     { fill: '#facc15', bg: 'rgba(250,204,21,0.12)', text: '#facc15', border: 'rgba(250,204,21,0.35)' },
  model:       { fill: '#c084fc', bg: 'rgba(192,132,252,0.12)', text: '#c084fc', border: 'rgba(192,132,252,0.35)' },
  config:      { fill: '#60a5fa', bg: 'rgba(96,165,250,0.12)', text: '#60a5fa', border: 'rgba(96,165,250,0.35)' },
  module:      { fill: '#94a3b8', bg: 'rgba(148,163,184,0.08)', text: '#94a3b8', border: 'rgba(148,163,184,0.2)' },
  test:        { fill: '#f87171', bg: 'rgba(248,113,113,0.08)', text: '#f87171', border: 'rgba(248,113,113,0.2)' },
}

// Compute positioned layout
const layout = computed(() => {
  const layers = graph.value.layers
  if (!layers.length) return { nodes: {}, width: 0, height: 0, layerY: [] }

  const positions = {}
  const layerY = []
  let y = PAD_TOP
  let maxW = 0

  for (const layer of layers) {
    const count = layer.files.length
    const rowW = count * NODE_W + (count - 1) * NODE_GAP + PAD_X * 2
    if (rowW > maxW) maxW = rowW
    layerY.push({ y, name: layer.name, type: layer.type })

    for (let i = 0; i < count; i++) {
      const x = PAD_X + i * (NODE_W + NODE_GAP)
      positions[layer.files[i]] = { x, y, layer: layer.type }
    }
    y += NODE_H + LAYER_GAP
  }

  return { nodes: positions, width: Math.max(maxW, 600), height: y + 20, layerY }
})

// SVG edge paths
const edgePaths = computed(() => {
  const pos = layout.value.nodes
  return graph.value.edges
    .filter(e => pos[e.source] && pos[e.target])
    .map(e => {
      const s = pos[e.source]
      const t = pos[e.target]
      const sx = s.x + NODE_W / 2
      const sy = s.y + NODE_H
      const tx = t.x + NODE_W / 2
      const ty = t.y
      const cy1 = sy + (ty - sy) * 0.4
      const cy2 = sy + (ty - sy) * 0.6
      return {
        d: `M${sx},${sy} C${sx},${cy1} ${tx},${cy2} ${tx},${ty}`,
        source: e.source,
        target: e.target,
      }
    })
})

function isHighlighted(edge) {
  if (!selected.value) return false
  return edge.source === selected.value || edge.target === selected.value
}

function isDimmed(path) {
  if (!selected.value) return false
  if (path === selected.value) return false
  const connected = graph.value.edges.some(
    e => (e.source === selected.value && e.target === path) ||
         (e.target === selected.value && e.source === path)
  )
  return !connected
}

function selectNode(path) {
  selected.value = selected.value === path ? null : path
}

const outEdges = computed(() => {
  if (!selected.value) return []
  return graph.value.edges.filter(e => e.source === selected.value)
})

const inEdges = computed(() => {
  if (!selected.value) return []
  return graph.value.edges.filter(e => e.target === selected.value)
})

function shortName(path) {
  const parts = path.split('/')
  return parts.length > 1 ? parts.slice(-1)[0] : path
}
</script>

<template>
  <div v-if="analysis" class="p-8 lg:px-10 flex flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-semibold">Dependency Tree</h1>
      <p class="text-sm text-text-secondary">
        {{ analysis.repo_name }} —
        {{ graph.nodes.length }} modules, {{ graph.edges.length }} dependencies
      </p>
      <p v-if="graph.nodes.length" class="text-xs text-text-muted mt-1">Click a node to highlight its connections</p>
    </div>

    <div v-if="!graph.nodes.length" class="bg-bg-surface rounded-xl p-8 text-center">
      <p class="text-text-muted text-sm">No internal dependencies detected.</p>
    </div>

    <template v-else>
      <div class="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-6">
        <!-- Graph canvas -->
        <div class="bg-bg-surface rounded-xl overflow-auto" ref="graphEl">
          <svg
            :width="layout.width"
            :height="layout.height"
            class="select-none"
          >
            <!-- Layer labels -->
            <g v-for="ly in layout.layerY" :key="ly.name">
              <text
                :x="12"
                :y="ly.y - 8"
                class="fill-text-tertiary"
                font-size="10"
                font-family="'JetBrains Mono', monospace"
                font-weight="600"
                letter-spacing="1.5"
              >{{ ly.name.toUpperCase() }}</text>
              <line
                :x1="12" :y1="ly.y - 2"
                :x2="layout.width - 12" :y2="ly.y - 2"
                stroke="currentColor"
                class="text-bg-inset"
                stroke-width="1"
                stroke-dasharray="4 4"
              />
            </g>

            <!-- Edges -->
            <path
              v-for="(edge, i) in edgePaths"
              :key="'e' + i"
              :d="edge.d"
              fill="none"
              :stroke="isHighlighted(edge) ? (edge.source === selected ? '#22d3ee' : '#22c55e') : 'rgba(148,163,184,0.15)'"
              :stroke-width="isHighlighted(edge) ? 2 : 1"
              :opacity="selected && !isHighlighted(edge) ? 0.3 : 1"
              class="transition-all duration-300"
            />

            <!-- Arrow markers on highlighted edges -->
            <circle
              v-for="(edge, i) in edgePaths.filter(e => isHighlighted(e))"
              :key="'dot' + i"
              :cx="layout.nodes[edge.target] ? layout.nodes[edge.target].x + NODE_W / 2 : 0"
              :cy="layout.nodes[edge.target] ? layout.nodes[edge.target].y - 3 : 0"
              r="3"
              :fill="edge.source === selected ? '#22d3ee' : '#22c55e'"
              class="transition-all duration-300"
            />

            <!-- Nodes -->
            <g
              v-for="(node, path) in layout.nodes"
              :key="path"
              :transform="`translate(${node.x}, ${node.y})`"
              @click="selectNode(path)"
              class="cursor-pointer"
              :opacity="isDimmed(path) ? 0.25 : 1"
              style="transition: opacity 0.3s"
            >
              <rect
                :width="NODE_W"
                :height="NODE_H"
                rx="8"
                :fill="typeStyle[nodeMap[path]?.node_type || 'module']?.bg"
                :stroke="selected === path
                  ? typeStyle[nodeMap[path]?.node_type || 'module']?.fill
                  : typeStyle[nodeMap[path]?.node_type || 'module']?.border"
                :stroke-width="selected === path ? 2 : 1"
                class="transition-all duration-200"
              />
              <text
                :x="NODE_W / 2"
                :y="NODE_H / 2 + 1"
                text-anchor="middle"
                dominant-baseline="middle"
                :fill="typeStyle[nodeMap[path]?.node_type || 'module']?.text"
                font-size="11"
                font-family="'JetBrains Mono', monospace"
                font-weight="500"
              >{{ shortName(path).length > 16 ? shortName(path).slice(0, 14) + '…' : shortName(path) }}</text>

              <!-- Import count badges -->
              <g v-if="nodeMap[path]?.imported_by_count > 0">
                <circle :cx="NODE_W - 4" :cy="4" r="8" fill="rgba(34,197,94,0.2)" />
                <text
                  :x="NODE_W - 4" :y="5"
                  text-anchor="middle" dominant-baseline="middle"
                  fill="#22c55e" font-size="8" font-family="'JetBrains Mono', monospace" font-weight="700"
                >{{ nodeMap[path].imported_by_count }}</text>
              </g>
            </g>
          </svg>
        </div>

        <!-- Detail panel -->
        <div class="flex flex-col gap-4">
          <div v-if="selected && nodeMap[selected]" class="bg-bg-surface rounded-xl p-5 flex flex-col gap-4 sticky top-8">
            <div class="flex items-center gap-2">
              <div
                class="w-3 h-3 rounded-full shrink-0"
                :style="{ background: typeStyle[nodeMap[selected].node_type]?.fill }"
              />
              <div class="flex flex-col min-w-0">
                <span class="font-mono text-sm font-semibold text-text-primary truncate">{{ shortName(selected) }}</span>
                <span class="font-mono text-[11px] text-text-muted truncate">{{ selected }}</span>
              </div>
            </div>

            <div class="flex gap-3">
              <div class="flex flex-col items-center gap-1 flex-1 bg-bg-inset rounded-lg py-3">
                <span class="font-mono text-lg font-bold text-accent">{{ nodeMap[selected].imports_count }}</span>
                <span class="text-[10px] text-text-muted">depends on</span>
              </div>
              <div class="flex flex-col items-center gap-1 flex-1 bg-bg-inset rounded-lg py-3">
                <span class="font-mono text-lg font-bold text-green-400">{{ nodeMap[selected].imported_by_count }}</span>
                <span class="text-[10px] text-text-muted">used by</span>
              </div>
            </div>

            <div v-if="outEdges.length" class="flex flex-col gap-1">
              <span class="text-[11px] font-semibold text-text-tertiary tracking-[1px]">DEPENDS ON</span>
              <button
                v-for="e in outEdges"
                :key="e.target"
                @click="selectNode(e.target)"
                class="flex items-center gap-2 py-1 text-left hover:bg-bg-inset/30 rounded px-1 transition-colors"
              >
                <span class="font-mono text-[11px] text-accent">→</span>
                <span class="font-mono text-xs text-text-secondary truncate">{{ e.target }}</span>
              </button>
            </div>

            <div v-if="inEdges.length" class="flex flex-col gap-1">
              <span class="text-[11px] font-semibold text-text-tertiary tracking-[1px]">USED BY</span>
              <button
                v-for="e in inEdges"
                :key="e.source"
                @click="selectNode(e.source)"
                class="flex items-center gap-2 py-1 text-left hover:bg-bg-inset/30 rounded px-1 transition-colors"
              >
                <span class="font-mono text-[11px] text-green-400">←</span>
                <span class="font-mono text-xs text-text-secondary truncate">{{ e.source }}</span>
              </button>
            </div>

            <div class="flex items-center gap-2 pt-2 border-t border-bg-inset">
              <span
                class="font-mono text-[10px] px-2 py-0.5 rounded"
                :style="{
                  background: typeStyle[nodeMap[selected].node_type]?.bg,
                  color: typeStyle[nodeMap[selected].node_type]?.text,
                }"
              >{{ nodeMap[selected].node_type }}</span>
              <span v-if="nodeMap[selected].subsystem" class="font-mono text-[10px] text-text-muted">
                {{ nodeMap[selected].subsystem }}
              </span>
            </div>
          </div>

          <!-- Legend -->
          <div class="bg-bg-surface rounded-xl p-4 flex flex-col gap-2">
            <span class="text-[10px] font-semibold text-text-tertiary tracking-[1px]">LEGEND</span>
            <div class="grid grid-cols-2 gap-1.5">
              <div v-for="(style, type) in typeStyle" :key="type" class="flex items-center gap-2">
                <div class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ background: style.fill }" />
                <span class="font-mono text-[10px] text-text-secondary">{{ type.replace('_', ' ') }}</span>
              </div>
            </div>
            <div class="flex items-center gap-3 mt-1">
              <div class="flex items-center gap-1">
                <div class="w-4 h-0 border-t border-accent"></div>
                <span class="text-[10px] text-text-muted">depends on</span>
              </div>
              <div class="flex items-center gap-1">
                <div class="w-4 h-0 border-t border-green-400"></div>
                <span class="text-[10px] text-text-muted">used by</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
