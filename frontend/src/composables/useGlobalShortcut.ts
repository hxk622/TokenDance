import { onMounted, onUnmounted } from 'vue'

interface ShortcutOptions {
  metaOrCtrl?: boolean
  preventDefault?: boolean
  enabled?: () => boolean
}

export function useGlobalShortcut(
  key: string,
  handler: (e: KeyboardEvent) => void,
  options: ShortcutOptions = {}
) {
  const { metaOrCtrl = false, preventDefault = true, enabled } = options
  
  const onKeydown = (e: KeyboardEvent) => {
    if (enabled && !enabled()) return
    if (metaOrCtrl && !(e.metaKey || e.ctrlKey)) return
    if (e.key.toLowerCase() !== key.toLowerCase()) return
    if (preventDefault) e.preventDefault()
    handler(e)
  }
  
  onMounted(() => {
    window.addEventListener('keydown', onKeydown)
  })
  
  onUnmounted(() => {
    window.removeEventListener('keydown', onKeydown)
  })
}
