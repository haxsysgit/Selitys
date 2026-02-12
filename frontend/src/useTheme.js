import { ref, watchEffect } from 'vue'

const theme = ref(localStorage.getItem('selitys-theme') || 'dark')

watchEffect(() => {
  const root = document.documentElement
  if (theme.value === 'light') {
    root.classList.add('light')
  } else {
    root.classList.remove('light')
  }
  localStorage.setItem('selitys-theme', theme.value)
})

export function useTheme() {
  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }
  return { theme, toggle }
}
