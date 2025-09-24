<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

const router = useRouter()
const loading = ref(false)
const list = ref([])

async function loadList() {
  loading.value = true
  try {
    const { data } = await api.get('/api/histories/')
    list.value = data
  } finally {
    loading.value = false
  }
}

async function createConversation() {
  loading.value = true
  try {
    const { data } = await api.post('/api/histories/', {})
    // 创建成功后跳转到聊天页面（通过id获取详情拿到session_id）
    router.push({ name: 'chat-detail', params: { id: data.id } })
  } finally {
    loading.value = false
  }
}

function openConversation(row) {
  router.push({ name: 'chat-detail', params: { id: row.id } })
}

onMounted(loadList)
</script>

<template>
  <div>
    <div style="margin-bottom:12px;display:flex;gap:8px;">
      <el-button type="primary" @click="createConversation" :loading="loading">新建会话</el-button>
      <el-button @click="loadList" :loading="loading">刷新</el-button>
    </div>

    <el-table :data="list" v-loading="loading" style="width:100%;">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="session_id" label="会话标识" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="openConversation(row)">进入聊天</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
