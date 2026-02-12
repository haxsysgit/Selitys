import { createRouter, createWebHistory } from 'vue-router'
import Overview from './pages/Overview.vue'
import AskView from './pages/AskView.vue'

const routes = [
  { path: '/', name: 'overview', component: Overview },
  { path: '/architecture', name: 'architecture', component: Overview },
  { path: '/request-flow', name: 'request-flow', component: Overview },
  { path: '/first-read', name: 'first-read', component: Overview },
  { path: '/config', name: 'config', component: Overview },
  { path: '/ask', name: 'ask', component: AskView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
