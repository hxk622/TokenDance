import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: {
      title: 'Login - TokenDance',
      requiresAuth: false
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: {
      title: 'Register - TokenDance',
      requiresAuth: false
    }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: {
      title: 'TokenDance - AI Agent Platform',
      requiresAuth: true
    }
  },
  {
    path: '/discover',
    name: 'Discover',
    component: () => import('@/views/SkillDiscovery.vue'),
    meta: {
      title: 'Discover Skills - TokenDance',
      requiresAuth: true
    }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/chat/:sessionId',
    name: 'ChatSession',
    component: () => import('@/views/ChatView.vue'),
    props: true,
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/demo',
    name: 'Demo',
    component: () => import('@/views/DemoView.vue'),
    meta: {
      requiresAuth: false
    }
  },
  {
    path: '/execution/:id',
    name: 'Execution',
    component: () => import('@/views/ExecutionPage.vue'),
    props: true,
    meta: {
      title: 'Task Execution',
      requiresAuth: false
    }
  },
  {
    path: '/files',
    name: 'Files',
    component: () => import('@/views/FilesView.vue'),
    meta: {
      title: 'Files - Coworker',
      requiresAuth: true
    }
  },
  {
    path: '/ppt/create',
    name: 'PPTCreate',
    component: () => import('@/views/PPTGenerateView.vue'),
    meta: {
      title: 'Create PPT - TokenDance',
      requiresAuth: true
    }
  },
  {
    path: '/ppt/edit/:id',
    name: 'PPTEdit',
    component: () => import('@/views/PPTEditView.vue'),
    props: true,
    meta: {
      title: 'Edit PPT - TokenDance',
      requiresAuth: true
    }
  },
  {
    path: '/ppt/preview/:id',
    name: 'PPTPreview',
    component: () => import('@/views/PPTEditView.vue'),
    props: true,
    meta: {
      title: 'Preview PPT - TokenDance',
      requiresAuth: true
    }
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// Navigation guards
router.beforeEach(async (to, _from, next) => {
  // Initialize auth store
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore()
  
  // Check if route requires authentication
  const requiresAuth = to.meta.requiresAuth !== false
  
  if (requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login page
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if ((to.name === 'Login' || to.name === 'Register') && authStore.isAuthenticated) {
    // Redirect authenticated users away from login/register
    next({ name: 'Home' })
  } else {
    next()
  }
})

export default router
