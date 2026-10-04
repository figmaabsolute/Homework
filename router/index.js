import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import { authState, restoreSession } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: { name: 'homework' } },
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { guestOnly: true } },
    { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue'), meta: { guestOnly: true } },
    {
      path: '/',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [
        { path: 'homework', name: 'homework', component: () => import('@/views/HomeworkView.vue') },
        { path: 'homework/:id', name: 'homework-detail', component: () => import('@/views/HomeworkDetailView.vue') },
        { path: 'schedule', name: 'schedule', component: () => import('@/views/ScheduleView.vue') },
        { path: 'profile', name: 'profile', component: () => import('@/views/ProfileView.vue') },
        { path: 'admin/subjects', name: 'subjects', component: () => import('@/views/SubjectsView.vue'), meta: { requiresStaff: true } },
        { path: 'admin/invites', name: 'invites', component: () => import('@/views/InvitesView.vue'), meta: { requiresStaff: true } },
      ],
    },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFoundView.vue') },
  ],
  scrollBehavior() {
    return { top: 0, behavior: 'smooth' }
  },
})

router.beforeEach(async (to) => {
  await restoreSession()
  const isAuthenticated = Boolean(authState.user)

  if (to.meta.requiresAuth && !isAuthenticated) {
    return { name: 'login', query: { next: to.fullPath } }
  }
  if (to.meta.requiresStaff && !authState.user?.is_staff) {
    return { name: 'homework' }
  }
  if (to.meta.guestOnly && isAuthenticated) {
    return { name: 'homework' }
  }
  return true
})

export default router
