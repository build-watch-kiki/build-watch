import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { failedTarget, isNavigating, navigationError } from '@/utils/navigation'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/projects'
  },
  {
    path: '/projects',
    component: () => import('@/layouts/BaseLayout.vue'),
    children: [
      {
        path: '',
        name: 'projects',
        component: () => import('@/views/project/Projects.vue'),
        meta: {
          title: 'Проекты'
        }
      }
    ]
  },
  {
    path: '/projects/:projectId',
    component: () => import('@/layouts/ProjectLayout.vue'),
    props: true,
    children: [
      {
        path: '',
        redirect: { name: 'project-dashboard' }
      },
      {
        path: 'dashboard',
        name: 'project-dashboard',
        component: () => import('@/views/project/dashboard/Dashboard.vue'),
        meta: {
          title: 'Мониторинг'
        }
      },
      {
        path: 'log',
        name: 'project-snapshots',
        component: () => import('@/views/project/snapshots/Snapshots.vue'),
        meta: {
          title: 'Журнал'
        }
      },
      {
        path: 'plan',
        name: 'project-plan',
        component: () => import('@/views/project/plan/Plan.vue'),
        meta: {
          title: 'Календарный план'
        }
      },
      {
        path: 'reference',
        name: 'project-reference',
        component: () => import('@/views/project/reference/Reference.vue'),
        meta: {
          title: 'Справочник'
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    component: () => import('@/layouts/BaseLayout.vue'),
    children: [
      {
        path: '',
        name: 'not-found',
        component: () => import('@/views/NotFound.vue'),
        meta: {
          title: 'Страница не найдена'
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to) => {
  isNavigating.value = true
  navigationError.value = null
  pendingTarget = to.fullPath
  if (to.params.projectId !== undefined) {
    const raw = to.params.projectId
    const id = Array.isArray(raw) ? raw[0] : raw
    if (!/^\d+$/.test(id as string)) {
      return { name: 'not-found' }
    }
  }
  return true
})

router.afterEach((to) => {
  isNavigating.value = false
  const title = to.meta.title as string | undefined
  document.title = title ? `BW: ${title}` : 'Build Watch'
})

let lastRetriedTarget: string | null = null
let pendingTarget: string | null = null

router.onError((error) => {
  isNavigating.value = false
  const message = error instanceof Error ? error.message : String(error)
  const isChunkError =
    /Failed to fetch dynamically imported module|Loading chunk|Importing a module script failed|error loading dynamically imported module/i.test(
      message
    )
  if (isChunkError && pendingTarget && pendingTarget !== lastRetriedTarget) {
    lastRetriedTarget = pendingTarget
    void router.replace(pendingTarget)
    return
  }
  failedTarget.value = pendingTarget
  navigationError.value = 'Не удалось открыть раздел'
})

export default router
