<script setup>
import { inject, ref, computed } from 'vue'
import Collapsible from '../components/Collapsible.vue'

const analysis = inject('analysis')

const selectedNode = ref(null)
const expandedLayers = ref(new Set())
const showEdgesFor = ref(null)

function toggleLayer(name) {
  expandedLayers.value.has(name)
    ? expandedLayers.value.delete(name)
    : expandedLayers.value.add(name)
}

function selectNode(path) {
  selectedNode.value = selectedNode.value === path ? null : path
  showEdgesFor.value = path
}

const graph = computed(() => analysis.value?.dependency_graph || { nodes: [], edges: [], layers: [] })

const nodeMap = computed(() => {
  const m = {}
  for (const n of graph.value.nodes) m[n.path] = n
  return m
})

const outEdges = computed(() => {
  if (!showEdgesFor.value) return []
  return graph.value.edges.filter(e => e.source === showEdgesFor.value)
})

const inEdges = computed(() => {
  if (!showEdgesFor.value) return []
  return graph.value.edges.filter(e => e.target === showEdgesFor.value)
})

const topImported = computed(() =>
  [...graph.value.nodes]
    .filter(n => n.imported_by_count > 0)
    .sort((a, b) => b.imported_by_count - a.imported_by_count)
    .slice(0, 8)
)

const typeColor = {
  entry_point: 'text-green-400',
  route: 'text-accent',
  service: 'text-yellow-400',
  model: 'text-purple-400',
  config: 'text-blue-400',
  module: 'text-text-tertiary',
  test: 'text-risk-high/60',
}

const typeBg = {
  entry_point: 'bg-green-400/10',
  route: 'bg-accent/10',
  service: 'bg-yellow-400/10',
  model: 'bg-purple-400/10',
  config: 'bg-blue-400/10',
  module: 'bg-bg-inset',
  test: 'bg-risk-high/5',
}

const typeIcon = {
  entry_point: '▶',
  route: '⇆',
  service: '⚡',
  model: '◇',
  config: '⚙',
  module: '○',
  test: '✓',
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
    </div>

    <div v-if="!graph.nodes.length" class="bg-bg-surface rounded-xl p-8 text-center">
      <p class="text-text-muted text-sm">No internal dependencies detected.</p>
    </div>

    <template v-else>
      <!-- Main layout: layers + detail panel -->
      <div class="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6">
        <!-- Architectural layers -->
        <div class="flex flex-col gap-4">
          <Collapsible title="ARCHITECTURAL LAYERS" :badge="graph.layers.length">
            <div class="flex flex-col gap-1">
              <div v-for="layer in graph.layers" :key="layer.name" class="flex flex-col">
                <button
                  @click="toggleLayer(layer.name)"
                  class="flex items-center gap-2 px-3 py-2.5 rounded-lg text-left hover:bg-bg-inset/50 transition-all duration-200 w-full group"
                >
                  <span
                    class="font-mono text-xs text-text-muted transition-transform duration-200"
                    :class="expandedLayers.has(layer.name) ? 'rotate-90' : ''"
                  >▸</span>
                  <span
                    class="font-mono text-xs font-bold px-1.5 py-0.5 rounded"
                    :class="[typeBg[layer.type], typeColor[layer.type]]"
                  >{{ typeIcon[layer.type] || '○' }}</span>
                  <span class="text-sm font-semibold text-text-primary">{{ layer.name }}</span>
                  <span class="font-mono text-[10px] text-text-muted bg-bg-inset px-1.5 py-0.5 rounded">
                    {{ layer.files.length }}
                  </span>
                </button>

                <div v-if="expandedLayers.has(layer.name)" class="ml-8 flex flex-col">
                  <button
                    v-for="(fpath, fi) in layer.files"
                    :key="fpath"
                    @click="selectNode(fpath)"
                    class="flex items-center gap-2 py-1.5 pl-3 border-l transition-all duration-200 text-left w-full"
                    :class="selectedNode === fpath
                      ? 'border-accent bg-accent/5'
                      : 'border-bg-surface hover:border-text-muted hover:bg-bg-inset/30'"
                  >
                    <span class="font-mono text-[11px] text-text-muted">{{ fi === layer.files.length - 1 ? '└' : '├' }}</span>
                    <span
                      class="font-mono text-xs truncate"
                      :class="selectedNode === fpath ? 'text-accent' : 'text-text-secondary'"
                    >{{ fpath }}</span>
                    <span
                      v-if="nodeMap[fpath]"
                      class="font-mono text-[10px] text-text-muted shrink-0"
                    >
                      <span v-if="nodeMap[fpath].imports_count">→{{ nodeMap[fpath].imports_count }}</span>
                      <span v-if="nodeMap[fpath].imported_by_count" class="ml-1">←{{ nodeMap[fpath].imported_by_count }}</span>
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </Collapsible>

          <!-- Top Dependencies table -->
          <Collapsible
            v-if="topImported.length"
            title="MOST DEPENDED-ON"
            :badge="topImported.length"
            badge-color="bg-green-400/10 text-green-400"
            :default-open="false"
          >
            <div class="flex flex-col gap-1">
              <div
                v-for="n in topImported"
                :key="n.path"
                class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-bg-inset/30 cursor-pointer transition-all duration-200"
                @click="selectNode(n.path)"
              >
                <span class="font-mono text-xs font-bold text-green-400 w-6 text-center">{{ n.imported_by_count }}</span>
                <div class="flex-1 min-w-0">
                  <span class="font-mono text-xs text-text-primary truncate block">{{ n.path }}</span>
                </div>
                <span
                  class="font-mono text-[10px] px-1.5 py-0.5 rounded shrink-0"
                  :class="[typeBg[n.node_type], typeColor[n.node_type]]"
                >{{ n.node_type }}</span>
              </div>
            </div>
          </Collapsible>
        </div>

        <!-- Detail panel (selected node) -->
        <div class="flex flex-col gap-4">
          <div v-if="selectedNode && nodeMap[selectedNode]" class="bg-bg-surface rounded-xl p-5 flex flex-col gap-4 sticky top-8">
            <div class="flex items-center gap-2">
              <span
                class="font-mono text-sm font-bold px-2 py-1 rounded"
                :class="[typeBg[nodeMap[selectedNode].node_type], typeColor[nodeMap[selectedNode].node_type]]"
              >{{ typeIcon[nodeMap[selectedNode].node_type] }}</span>
              <div class="flex flex-col min-w-0">
                <span class="font-mono text-sm font-semibold text-text-primary truncate">{{ nodeMap[selectedNode].label }}</span>
                <span class="font-mono text-[11px] text-text-muted truncate">{{ selectedNode }}</span>
              </div>
            </div>

            <div class="flex gap-4">
              <div class="flex flex-col items-center gap-1 flex-1 bg-bg-inset rounded-lg py-3">
                <span class="font-mono text-lg font-bold text-accent">{{ nodeMap[selectedNode].imports_count }}</span>
                <span class="text-[10px] text-text-muted">imports</span>
              </div>
              <div class="flex flex-col items-center gap-1 flex-1 bg-bg-inset rounded-lg py-3">
                <span class="font-mono text-lg font-bold text-green-400">{{ nodeMap[selectedNode].imported_by_count }}</span>
                <span class="text-[10px] text-text-muted">imported by</span>
              </div>
            </div>

            <!-- Outgoing edges -->
            <div v-if="outEdges.length" class="flex flex-col gap-1">
              <span class="text-[11px] font-semibold text-text-tertiary tracking-[1px]">DEPENDS ON</span>
              <div
                v-for="e in outEdges"
                :key="e.target"
                class="flex items-center gap-2 py-1"
              >
                <span class="font-mono text-[11px] text-accent">→</span>
                <span class="font-mono text-xs text-text-secondary truncate">{{ e.target }}</span>
              </div>
            </div>

            <!-- Incoming edges -->
            <div v-if="inEdges.length" class="flex flex-col gap-1">
              <span class="text-[11px] font-semibold text-text-tertiary tracking-[1px]">USED BY</span>
              <div
                v-for="e in inEdges"
                :key="e.source"
                class="flex items-center gap-2 py-1"
              >
                <span class="font-mono text-[11px] text-green-400">←</span>
                <span class="font-mono text-xs text-text-secondary truncate">{{ e.source }}</span>
              </div>
            </div>
          </div>

          <div v-else class="bg-bg-surface rounded-xl p-8 flex items-center justify-center">
            <p class="text-text-muted text-sm text-center">Click a file in the layer tree to see its dependencies</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
