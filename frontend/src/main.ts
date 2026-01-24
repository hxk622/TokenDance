console.log('[Main] Script start - before any imports')

console.log('[Main] Importing vue...')
import { createApp } from 'vue'
console.log('[Main] vue imported')

console.log('[Main] Importing pinia...')
import { createPinia } from 'pinia'
console.log('[Main] pinia imported')

console.log('[Main] Importing App.vue...')
import App from './App.vue'
console.log('[Main] App.vue imported')

console.log('[Main] Importing router...')
import router from './router'
console.log('[Main] router imported')

console.log('[Main] Importing Token Manager...')
import { tokenManager } from './utils/tokenManager'
console.log('[Main] Token Manager imported')

console.log('[Main] Importing design-system.css...')
import './assets/design-system.css'
console.log('[Main] design-system.css imported')

console.log('[Main] Importing main.css...')
import './assets/main.css'
console.log('[Main] main.css imported')

console.log('[Main] Importing vibe.css...')
import './styles/vibe.css'
console.log('[Main] vibe.css imported')

console.log('[Main] Importing vibe-animations.css...')
import './styles/vibe-animations.css'
console.log('[Main] vibe-animations.css imported')

console.log('[Main] Importing glass-morphism.css...')
import './styles/glass-morphism.css'
console.log('[Main] glass-morphism.css imported')

console.log('[Main] Importing micro-interactions.css...')
import './styles/micro-interactions.css'
console.log('[Main] micro-interactions.css imported')

console.log('[Main] Importing anygen.css...')
import './styles/anygen.css'
console.log('[Main] anygen.css imported')

console.log('[Main] All imports done, creating app')
const app = createApp(App)

console.log('[Main] Installing Pinia')
app.use(createPinia())

console.log('[Main] Installing Router')
app.use(router)

console.log('[Main] Mounting app')
app.mount('#app')
console.log('[Main] App mounted')

// Initialize Token Manager if user is logged in
console.log('[Main] Initializing Token Manager')
if (localStorage.getItem('access_token')) {
  tokenManager.init()
  console.log('[Main] Token Manager initialized')
} else {
  console.log('[Main] No token found, Token Manager not initialized')
}
