<script setup>
import { ref, reactive, onMounted } from 'vue'
import dayjs from 'dayjs'
import api from '../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { jwtDecode } from 'jwt-decode'

const auth = useAuthStore()

function getUserId() {
  // 优先使用登录后存储的 user_id；若不存在就从 access 解析
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
const dialogTitle = ref('新建待办')
const formRef = ref()
const form = reactive({
  id: null,
  title: '',
  description: '',
  due_date: '',
  completed: false,
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  description: [{ required: true, message: '请输入描述', trigger: 'blur' }],
}

async function fetchList() {
  loading.value = true
  errorMsg.value = ''
  try {
    const { data } = await api.get('/api/todos/')
    list.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e) {
    errorMsg.value = '加载失败'
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialogTitle.value = '新建待办'
  Object.assign(form, {
    id: null,
    title: '',
    description: '',
    due_date: '',
    completed: false,
  })
  dialogVisible.value = true
}

function openEdit(row) {
  dialogTitle.value = '编辑待办'
  Object.assign(form, {
    id: row.id,
    title: row.title,
    description: row.description,
    due_date: row.due_date ? dayjs(row.due_date).format('YYYY-MM-DD HH:mm:ss') : '',
    completed: row.completed,
  })
  dialogVisible.value = true
}

async function submitForm() {
  await formRef.value.validate()
  const payload = {
    title: form.title,
    description: form.description,
    due_date: form.due_date ? dayjs(form.due_date).toISOString() : null,
    completed: form.completed,
  }

  try {
    if (form.id) {
      await api.put(`/api/todos/${form.id}/`, payload)
    } else {
      await api.post('/api/todos/', payload)
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
    await api.delete(`/api/todos/${row.id}/`)
    await fetchList()
    ElMessage.success('删除成功')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function toggleCompleted(row) {
  try {
    await api.patch(`/api/todos/${row.id}/`, { completed: row.completed })
    ElMessage.success('状态已更新')
  } catch (e) {
    row.completed = !row.completed
    ElMessage.error('更新失败')
  }
}

onMounted(fetchList)
</script>

<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span>待办事项</span>
        <el-button type="primary" @click="openCreate">新建</el-button>
      </div>
    </template>

    <el-alert v-if="errorMsg" type="error" :closable="false" :title="errorMsg" style="margin-bottom:12px;" />

    <el-skeleton v-if="loading" :rows="5" animated />
    <el-empty v-else-if="!list.length" description="暂无数据" />
    <el-table v-else :data="list" style="width: 100%">
      <el-table-column prop="id" label="ID" width="90" />
      <el-table-column prop="title" label="标题" min-width="180" />
      <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
      <el-table-column label="截止时间" min-width="180">
        <template #default="{ row }">
          <span>{{ row.due_date ? dayjs(row.due_date).format('YYYY-MM-DD HH:mm') : '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="完成" width="120">
        <template #default="{ row }">
          <el-switch v-model="row.completed" @change="() => toggleCompleted(row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" placeholder="请输入标题" />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input v-model="form.description" placeholder="请输入描述" type="textarea" :rows="3" />
      </el-form-item>
      <el-form-item label="截止时间">
        <el-date-picker
          v-model="form.due_date"
          type="datetime"
          value-format="YYYY-MM-DD HH:mm:ss"
          placeholder="选择日期时间"
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