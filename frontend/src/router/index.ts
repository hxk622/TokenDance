console.log('[Router] Module start - before imports')

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

console.log('[Router] Imports done, defining routes')

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
    path: '/auth/wechat/callback',
    name: 'WeChatCallback',
    component: () => import('@/views/LoginView.vue'),
    meta: {
      title: 'WeChat Login - TokenDance',
      requiresAuth: false
    }
  },
  {
    path: '/auth/gmail/callback',
    name: 'GmailCallback',
    component: () => import('@/views/LoginView.vue'),
    meta: {
      title: 'Gmail Login - TokenDance',
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
  {
    path: '/financial-test',
    name: 'FinancialTest',
    component: () => import('@/views/FinancialTest.vue'),
    meta: {
      title: 'Financial Test - TokenDance',
      requiresAuth: false
    }
  },
  {
    path: '/financial',
    name: 'FinancialAnalysis',
    component: () => import('@/views/FinancialAnalysis.vue'),
    meta: {
      title: '投研工作台 - TokenDance',
      requiresAuth: false
    }
  },
  {
    path: '/rendering-demo',
    name: 'RenderingDemo',
    component: () => import('@/views/RenderingDemo.vue'),
    meta: {
      title: '渲染引擎演示 - TokenDance',
      requiresAuth: false
    }
  },
]

console.log('[Router] Routes defined, creating router instance')
console.log('[Router] BASE_URL:', import.meta.env.BASE_URL)

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})
console.log('[Router] Router instance created')

// Navigation guards
console.log('[Router] Setting up beforeEach guard')
router.beforeEach(async (to, _from, next) => {
  console.log('[Router] beforeEach start, to:', to.path)
  
  // Initialize auth store
  console.log('[Router] importing auth store')
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore()
  console.log('[Router] auth store loaded, isAuthenticated:', authStore.isAuthenticated)
  
  // Check if route requires authentication
  const requiresAuth = to.meta.requiresAuth !== false
  console.log('[Router] requiresAuth:', requiresAuth)
  
  if (requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login page
    console.log('[Router] not authenticated, redirecting to login')
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if ((to.name === 'Login' || to.name === 'Register') && authStore.isAuthenticated) {
    // Redirect authenticated users away from login/register
    console.log('[Router] authenticated user on login/register, redirecting to home')
    next({ name: 'Home' })
  } else {
    console.log('[Router] proceeding to', to.path)
    next()
  }
})

console.log('[Router] Module setup complete, exporting router')
export default router
