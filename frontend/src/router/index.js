import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: { name: 'todos' } },
    { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
    { path: '/register', name: 'register', component: () => import('../views/RegisterView.vue') },
    { path: '/todos', name: 'todos', component: () => import('../views/TodosView.vue'), meta: { requiresAuth: true, title: '待办事项' } },
    { path: '/leetcode', name: 'leetcode', component: () => import('../views/LeetCodeView.vue'), meta: { requiresAuth: true, title: 'LeetCode题目' } },
    { path: '/leetcode/:id', name: 'leetcode-detail', component: () => import('../views/LeetCodeDetail.vue'), meta: { requiresAuth: true, title: '题目详情' } },

    { path: '/accounts', name: 'accounts', component: () => import('../views/AccountList.vue'), meta: { requiresAuth: true, title: '账户列表' } },
    { path: '/transactions', name: 'transactions', component: () => import('../views/TransactionList.vue'), meta: { requiresAuth: true, title: '交易记录' } },
    { path: '/categories', name: 'categories', component: () => import('../views/CategoryManagement.vue'), meta: { requiresAuth: true, title: '分类管理' } },
    { path: '/statistics', name: 'statistics', component: () => import('../views/Statistics.vue'), meta: { requiresAuth: true, title: '统计报表' } },
    { path: '/conversations', name: 'conversations', component: () => import('../views/ConversationList.vue'), meta: { requiresAuth: true, title: '会话列表' } },
    { path: '/chat/:id', name: 'chat-detail', component: () => import('../views/Chat.vue'), meta: { requiresAuth: true, title: '聊天' } },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
})

export default router