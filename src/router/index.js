import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import UserLots from '../views/UserLots.vue'
import UserReservations from '../views/UserReservations.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/login', name: 'Login', component: Login },
  { path: '/register', name: 'Register', component: Register },
  {
    path: '/user/dashboard',
    alias: '/user-dashboard',         // ← this line makes /user-dashboard work too
    name: 'UserLots',
    component: UserLots,
    meta: { requiresAuth: true, role: 'user' }
  },
  {
    path: '/user/reservations',
    name: 'UserReservations',
    component: UserReservations,
    meta: { requiresAuth: true, role: 'user' }
  },
  {
    path: '/admin-dashboard',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true, role: 'admin' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')

  if (to.meta.requiresAuth) {
    if (!token) return next('/login')
    if (to.meta.role && role !== to.meta.role) return next('/')
  }

  next()
})

export default router
