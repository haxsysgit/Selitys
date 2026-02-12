import { createRouter, createWebHistory } from 'vue-router'
import Overview from './pages/Overview.vue'
import ArchitectureView from './pages/ArchitectureView.vue'
import RequestFlowView from './pages/RequestFlowView.vue'
import FirstReadView from './pages/FirstReadView.vue'
import ConfigView from './pages/ConfigView.vue'
import AskView from './pages/AskView.vue'

const routes = [
  { path: '/', name: 'overview', component: Overview },
  { path: '/architecture', name: 'architecture', component: ArchitectureView },
  { path: '/request-flow', name: 'request-flow', component: RequestFlowView },
  { path: '/first-read', name: 'first-read', component: FirstReadView },
  { path: '/config', name: 'config', component: ConfigView },
  { path: '/ask', name: 'ask', component: AskView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
