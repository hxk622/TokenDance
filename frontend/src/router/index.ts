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
      title: 'Login - TokenDance'
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: {
      title: 'Register - TokenDance'
    }
  },
  {
    path: '/auth/wechat/callback',
    name: 'WeChatCallback',
    component: () => import('@/views/LoginView.vue'),
    meta: {
      title: 'WeChat Login - TokenDance'
    }
  },
  {
    path: '/auth/gmail/callback',
    name: 'GmailCallback',
    component: () => import('@/views/LoginView.vue'),
    meta: {
      title: 'Gmail Login - TokenDance'
    }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: {
      title: 'TokenDance - AI Agent Platform'
    }
  },
  {
    path: '/discover',
    name: 'Discover',
    component: () => import('@/views/SkillDiscovery.vue'),
    meta: {
      title: 'Discover Skills - TokenDance'
    }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue'),
    meta: {
      title: 'Chat - TokenDance'
    }
  },
  {
    path: '/chat/:sessionId',
    name: 'ChatSession',
    component: () => import('@/views/ChatView.vue'),
    props: true,
    meta: {
      title: 'Chat - TokenDance'
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
      title: 'Task Execution'
    }
  },
  {
    path: '/files',
    name: 'Files',
    component: () => import('@/views/FilesView.vue'),
    meta: {
      title: 'Files - Coworker'
    }
  },
  {
    path: '/ppt/create',
    name: 'PPTCreate',
    component: () => import('@/views/PPTGenerateView.vue'),
    meta: {
      title: 'Create PPT - TokenDance'
    }
  },
  {
    path: '/ppt/edit/:id',
    name: 'PPTEdit',
    component: () => import('@/views/PPTEditView.vue'),
    props: true,
    meta: {
      title: 'Edit PPT - TokenDance'
    }
  },
  {
    path: '/ppt/preview/:id',
    name: 'PPTPreview',
    component: () => import('@/views/PPTEditView.vue'),
    props: true,
    meta: {
      title: 'Preview PPT - TokenDance'
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

// Navigation guards - simplified for guest mode
console.log('[Router] Setting up beforeEach guard')
router.beforeEach(async (to, _from, next) => {
  console.log('[Router] beforeEach start, to:', to.path)
  
  // Initialize auth store (to restore session if token exists)
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore()
  
  // If we have a token but no user, try to initialize
  if (authStore.accessToken && !authStore.user) {
    console.log('[Router] has token but no user, initializing...')
    try {
      await authStore.initialize()
    } catch (e) {
      console.error('[Router] initialize failed:', e)
    }
  }
  
  // Guest mode: allow all routes without login
  // Only redirect authenticated users away from login/register pages
  if ((to.name === 'Login' || to.name === 'Register') && authStore.isAuthenticated) {
    console.log('[Router] authenticated user on login/register, redirecting to home')
    next({ name: 'Home' })
  } else {
    console.log('[Router] proceeding to', to.path)
    next()
  }
})

console.log('[Router] Module setup complete, exporting router')
export default router
