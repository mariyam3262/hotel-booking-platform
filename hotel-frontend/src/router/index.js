import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import PropertiesView from '../views/PropertiesView.vue'

import BookingCreateView from '../views/BookingCreateView.vue'
import PropertyDetailView from '../views/PropertyDetailView.vue'
import BookingDetailView from '../views/BookingDetailView.vue'
import DashboardView from '../views/DashboardView.vue'
import ConciergeView from '../views/ConciergeView.vue'
import PropertyCreateView from '../views/PropertyCreateView.vue'
import StaffAdminView from '../views/StaffAdminView.vue'

const routes = [
  { path: '/login', component: LoginView },
  { path: '/', component: PropertiesView, meta: { requiresAuth: true } },
  { path: '/dashboard', component: DashboardView, meta: { requiresAuth: true } },
  { path: '/properties/:id', component: PropertyDetailView, meta: { requiresAuth: true } },
  { path: '/bookings/new', component: BookingCreateView, meta: { requiresAuth: true } },
  { path: '/bookings/:id', component: BookingDetailView, meta: { requiresAuth: true } },
  { path: '/concierge', component: ConciergeView, meta: { requiresAuth: true } },
  { path: '/properties/new', component: PropertyCreateView, meta: { requiresAuth: true } },
  { path: '/admin/properties/:id/staff', component: StaffAdminView, meta: { requiresAuth: true } },


]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return '/login'
  }
})

export default router