import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue')
  },
  {
    path: '/chat',
    redirect: '/'
  },
  {
    path: '/chat/:sessionId',
    name: 'ChatSession',
    component: () => import('@/views/ChatView.vue'),
    props: true
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('@/views/HomeView.vue')
  },
  {
    path: '/demo',
    name: 'Demo',
    component: () => import('@/views/DemoView.vue')
  },
  {
    path: '/execution/:id',
    name: 'Execution',
    component: () => import('@/views/ExecutionPage.vue'),
    props: true,
    meta: {
      title: 'Task Execution',
      requiresAuth: false  // MVP阶段暂不需要认证
    }
  },
  // TODO: Add more routes
  // {
  //   path: '/login',
  //   name: 'Login',
  //   component: () => import('@/views/Auth/LoginView.vue')
  // },
  // {
  //   path: '/workspaces',
  //   name: 'Workspaces',
  //   component: () => import('@/views/WorkspaceListView.vue'),
  //   meta: { requiresAuth: true }
  // },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// Navigation guards
router.beforeEach((_to, _from, next) => {
  // TODO: Add authentication check
  // const authStore = useAuthStore()
  // if (to.meta.requiresAuth && !authStore.isAuthenticated) {
  //   next({ name: 'Login' })
  // } else {
  //   next()
  // }
  next()
})

export default router
