<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const list = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增分类')
const formRef = ref()
const form = reactive({
  id: null,
  name: '',
  type: 'expense',
  description: ''
})
const rules = {
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
}

async function fetchList() {
  loading.value = true
  try {
    const { data } = await api.get('/api/categories/')
    list.value = Array.isArray(data) ? data : (data.results || [])
  } finally { loading.value = false }
}

function openCreate() {
  dialogTitle.value = '新增分类'
  Object.assign(form, { id: null, name: '', type: 'expense', description: '' })
  dialogVisible.value = true
}
function openEdit(row) {
  dialogTitle.value = '编辑分类'
  Object.assign(form, row)
  dialogVisible.value = true
}
async function submitForm() {
  await formRef.value.validate()
  const payload = { name: form.name, type: form.type, description: form.description }
  try {
    if (form.id) await api.put(`/api/categories/${form.id}/`, payload)
    else await api.post('/api/categories/', payload)
    dialogVisible.value = false
    await fetchList()
    ElMessage.success('保存成功')
  } catch { ElMessage.error('保存失败') }
}
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除分类「${row.name}」？`, '提示', { type: 'warning' })
    await api.delete(`/api/categories/${row.id}/`)
    await fetchList()
    ElMessage.success('删除成功')
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

onMounted(fetchList)
</script>

<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span>分类管理</span>
        <el-button type="primary" @click="openCreate">新增</el-button>
      </div>
    </template>

    <el-table :data="list" v-loading="loading" style="width:100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" min-width="160" />
      <el-table-column prop="type" label="类型" width="120">
        <template #default="{ row }">
          <el-tag :type="row.type === 'income' ? 'success' : 'danger'">
            {{ row.type === 'income' ? '收入' : '支出' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="备注" min-width="240" show-overflow-tooltip />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item label="类型" prop="type">
        <el-select v-model="form.type" placeholder="请选择">
          <el-option label="收入" value="income" />
          <el-option label="支出" value="expense" />
        </el-select>
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.description" type="textarea" :rows="3" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="submitForm">保存</el-button>
    </template>
  </el-dialog>
</template>
