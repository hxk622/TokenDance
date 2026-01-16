import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import './styles/vibe.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// Initialize auth store
const { useAuthStore } = await import('@/stores/auth')
const authStore = useAuthStore()
await authStore.initialize()

app.mount('#app')
