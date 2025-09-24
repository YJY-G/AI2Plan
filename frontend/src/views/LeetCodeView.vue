<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { jwtDecode } from 'jwt-decode'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

function getUserId() {
  if (auth?.user?.user_id) return auth.user.user_id
  try {
    const access = auth?.access || localStorage.getItem('access') || ''
    return access ? jwtDecode(access).user_id : null
  } catch {
    return null
  }
}

const loading = ref(false)
const list = ref([])
const errorMsg = ref('')

const dialogVisible = ref(false)
const dialogTitle = ref('新建题目')
const formRef = ref()
const form = reactive({
  id: null,
  title: '',
  difficulty: 'easy',
  description: '',
  solution: '',
  thinking: '',
  completed: false,
})

const difficultyOptions = [
  { label: '简单', value: 'easy' },
  { label: '中等', value: 'medium' },
  { label: '困难', value: 'hard' },
]

const rules = {
  title: [{ required: true, message: '请输入题目名称', trigger: 'blur' }],
  difficulty: [{ required: true, message: '请选择难度', trigger: 'change' }],
  description: [{ required: true, message: '请输入题目描述', trigger: 'blur' }],
  solution: [{ required: true, message: '请输入解题方法', trigger: 'blur' }],
  thinking: [{ required: true, message: '请输入解题思路', trigger: 'blur' }],
}

async function fetchList() {
  loading.value = true
  errorMsg.value = ''
  try {
    const { data } = await api.get('/api/leetcode/')
    list.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e) {
    errorMsg.value = '加载失败'
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialogTitle.value = '新建题目'
  Object.assign(form, {
    id: null,
    title: '',
    difficulty: 'easy',
    description: '',
    solution: '',
    thinking: '',
    completed: false,
  })
  dialogVisible.value = true
}

function openEdit(row) {
  dialogTitle.value = '编辑题目'
  Object.assign(form, {
    id: row.id,
    title: row.title,
    difficulty: row.difficulty,
    description: row.description,
    solution: row.solution,
    thinking: row.thinking,
    completed: row.completed,
  })
  dialogVisible.value = true
}

async function submitForm() {
  await formRef.value.validate()
  const payload = {
    title: form.title,
    difficulty: form.difficulty,
    description: form.description,
    solution: form.solution,
    thinking: form.thinking,
    completed: form.completed,
  }

  try {
    if (form.id) {
      await api.put(`/api/leetcode/${form.id}/`, payload)
    } else {
      await api.post('/api/leetcode/', payload)
    }
    dialogVisible.value = false
    await fetchList()
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除「${row.title}」吗？`, '提示', { type: 'warning' })
    await api.delete(`/api/leetcode/${row.id}/`)
    await fetchList()
    ElMessage.success('删除成功')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function toggleCompleted(row) {
  try {
    await api.patch(`/api/leetcode/${row.id}/`, { completed: row.completed })
    ElMessage.success('状态已更新')
  } catch (e) {
    row.completed = !row.completed
    ElMessage.error('更新失败')
  }
}

function goToDetail(row) {
  router.push({ name: 'leetcode-detail', params: { id: row.id } })
}

function getDifficultyColor(difficulty) {
  const colors = {
    easy: 'success',
    medium: 'warning', 
    hard: 'danger'
  }
  return colors[difficulty] || 'info'
}

function getDifficultyText(difficulty) {
  const texts = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return texts[difficulty] || '未知'
}

onMounted(fetchList)
</script>

<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span>LeetCode 题目管理</span>
        <el-button type="primary" @click="openCreate">新建题目</el-button>
      </div>
    </template>

    <el-alert v-if="errorMsg" type="error" :closable="false" :title="errorMsg" style="margin-bottom:12px;" />

    <el-skeleton v-if="loading" :rows="5" animated />
    <el-empty v-else-if="!list.length" description="暂无数据" />
    <el-table v-else :data="list" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="难度" width="100">
        <template #default="{ row }">
          <el-tag :type="getDifficultyColor(row.difficulty)" size="small">
            {{ getDifficultyText(row.difficulty) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="题目名称" min-width="300">
        <template #default="{ row }">
          <el-button 
            type="primary" 
            link 
            @click="goToDetail(row)"
            style="padding: 0; font-size: 14px; text-align: left; justify-content: flex-start;"
          >
            {{ row.title }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="完成状态" width="120">
        <template #default="{ row }">
          <el-switch v-model="row.completed" @change="() => toggleCompleted(row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <div style="display: flex; gap: 8px; padding-right: 12px;">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="800px" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="题目名称" prop="title">
        <el-input v-model="form.title" placeholder="请输入题目名称" />
      </el-form-item>
      <el-form-item label="难度" prop="difficulty">
        <el-select v-model="form.difficulty" placeholder="请选择难度">
          <el-option
            v-for="option in difficultyOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="题目描述" prop="description">
        <el-input 
          v-model="form.description" 
          placeholder="请输入题目描述" 
          type="textarea" 
          :rows="4" 
        />
      </el-form-item>
      <el-form-item label="解题方法" prop="solution">
        <el-input 
          v-model="form.solution" 
          placeholder="请输入解题方法/代码" 
          type="textarea" 
          :rows="6" 
        />
      </el-form-item>
      <el-form-item label="解题思路" prop="thinking">
        <el-input 
          v-model="form.thinking" 
          placeholder="请输入解题思路" 
          type="textarea" 
          :rows="4" 
        />
      </el-form-item>
      <el-form-item label="完成状态">
        <el-switch v-model="form.completed" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="submitForm">保存</el-button>
    </template>
  </el-dialog>
</template>

<style scoped></style>
