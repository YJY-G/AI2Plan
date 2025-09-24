<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const active = computed(() => (route.name ? String(route.name) : ''))

function onSelect(index) {
  const map = { 
    todos: 'todos', 
    leetcode: 'leetcode',
    accounts: 'accounts', 
    transactions: 'transactions', 
    categories: 'categories', 
    statistics: 'statistics', 
    conversations: 'conversations' 
  }
  if (map[index]) router.push({ name: map[index] })
}

function handleLogout() {
  auth.logout()
  router.replace({ name: 'login' })
}
</script>

<template>
  <el-config-provider>
    <el-container style="height:100vh;">
      <el-aside v-if="auth.isAuthenticated" width="220px" style="border-right:1px solid var(--el-border-color);">
        <div style="height:60px;display:flex;align-items:center;justify-content:center;font-weight:600;">
          AI2Plan
        </div>
        <el-menu :default-active="active" @select="onSelect" router>
          <el-menu-item index="todos"><span>待办事项</span></el-menu-item>
          <el-menu-item index="leetcode"><span>LeetCode题目</span></el-menu-item>
          <el-sub-menu index="accounting">
            <template #title>记账</template>
            <el-menu-item index="accounts">账户列表</el-menu-item>
            <el-menu-item index="transactions">交易记录</el-menu-item>
            <el-menu-item index="categories">分类管理</el-menu-item>
            <el-menu-item index="statistics">统计报表</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="chat">
            <template #title>聊天</template>
            <el-menu-item index="conversations">会话列表</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header style="display:flex;align-items:center;justify-content:space-between;">
          <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-weight:600;">AI2Plan 管理台</span>
            <span v-if="route.meta && route.meta.title" style="color:#909399;">/ {{ route.meta.title }}</span>
          </div>
          <div v-if="auth.isAuthenticated" style="display:flex;align-items:center;gap:12px;">
            <el-tag type="info" effect="light">{{ auth.user?.username }}</el-tag>
            <el-button type="danger" @click="handleLogout">退出</el-button>
          </div>
        </el-header>

        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </el-config-provider>
</template>

<style scoped></style>