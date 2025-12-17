
import { createRouter, createWebHistory } from 'vue-router'

import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import Farm from '@/views/Farm.vue'
import Encounter from '@/views/Encounter.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    component: Login
  },
  {
    path: '/register',
    component: Register
  },
  {
    path: '/farm',
    component: Farm 
  },
  {
    path: '/BuildPanel',
    component: Farm 
  },
  {
    path: '/Encounter',
    component: Encounter
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
