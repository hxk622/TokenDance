import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
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
    component: () => import('@/views/ChatView.vue')
  },
  {
    path: '/chat/:sessionId',
    name: 'ChatSession',
    component: () => import('@/views/ChatView.vue'),
    props: true
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
  {
    path: '/files',
    name: 'Files',
    component: () => import('@/views/FilesView.vue'),
    meta: {
      title: 'Files - Coworker',
      requiresAuth: false
    }
  },
  {
    path: '/ppt/create',
    name: 'PPTCreate',
    component: () => import('@/views/PPTGenerateView.vue'),
    meta: {
      title: 'Create PPT - TokenDance',
      requiresAuth: false
    }
  },
  {
    path: '/ppt/edit/:id',
    name: 'PPTEdit',
    component: () => import('@/views/PPTEditView.vue'),
    props: true,
    meta: {
      title: 'Edit PPT - TokenDance',
      requiresAuth: false
    }
  },
  {
    path: '/ppt/preview/:id',
    name: 'PPTPreview',
    component: () => import('@/views/PPTEditView.vue'),  // 复用编辑页，后续可单独创建
    props: true,
    meta: {
      title: 'Preview PPT - TokenDance',
      requiresAuth: false
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
