<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import api from '../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'

const loading = ref(false)
const list = ref([])

const accounts = ref([])
const categories = ref([])

const filters = reactive({
  dateRange: [],
  type: '',
  account: '',
  category: '',
  keyword: '',
  sort: '-date' // -date/ date/ -amount/ amount
})

const dialogVisible = ref(false)
const dialogTitle = ref('新增交易')
const formRef = ref()
const form = reactive({
  id: null,
  date: dayjs().format('YYYY-MM-DD'),
  amount: 0,
  description: '',
  category: null,   // 传分类 id
  account: null,    // 传账户 id
  transaction_type: 'expense'
})
const rules = {
  date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  account: [{ required: true, message: '请选择账户', trigger: 'change' }],
  transaction_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
}

async function fetchMaster() {
  const [accRes, catRes] = await Promise.all([
    api.get('/api/accounts/'),
    api.get('/api/categories/')
  ])
  accounts.value = Array.isArray(accRes.data) ? accRes.data : (accRes.data.results || [])
  categories.value = Array.isArray(catRes.data) ? catRes.data : (catRes.data.results || [])
}
async function fetchList() {
  loading.value = true
  try {
    const { data } = await api.get('/api/transactions/')
    const raw = Array.isArray(data) ? data : (data.results || [])
    list.value = raw
  } finally { loading.value = false }
}

const filtered = computed(() => {
  let data = list.value.slice()

  if (filters.type) data = data.filter(x => x.transaction_type === filters.type)
  if (filters.account) data = data.filter(x => String(x.account) === String(filters.account))
  if (filters.category) data = data.filter(x => String(x.category) === String(filters.category))
  if (filters.keyword) data = data.filter(x =>
    (x.description || '').toLowerCase().includes(filters.keyword.toLowerCase())
  )
  if (filters.dateRange?.length === 2) {
    const [start, end] = filters.dateRange
    const s = dayjs(start).startOf('day')
    const e = dayjs(end).endOf('day')
    data = data.filter(x => dayjs(x.date).isAfter(s.subtract(1, 'ms')) && dayjs(x.date).isBefore(e.add(1, 'ms')))
  }

  const sortKey = filters.sort.replace('-', '')
  const desc = filters.sort.startsWith('-')
  data.sort((a,b) => {
    const va = sortKey === 'amount' ? Number(a.amount) : new Date(a.date).getTime()
    const vb = sortKey === 'amount' ? Number(b.amount) : new Date(b.date).getTime()
    return desc ? vb - va : va - vb
  })
  return data
})

function resetFilters() {
  Object.assign(filters, { dateRange: [], type: '', account: '', category: '', keyword: '', sort: '-date' })
}

function openCreate() {
  dialogTitle.value = '新增交易'
  Object.assign(form, {
    id: null,
    date: dayjs().format('YYYY-MM-DD'),
    amount: 0,
    description: '',
    category: null,
    account: null,
    transaction_type: 'expense'
  })
  dialogVisible.value = true
}
function openEdit(row) {
  dialogTitle.value = '编辑交易'
  Object.assign(form, {
    id: row.id,
    date: row.date,
    amount: row.amount,
    description: row.description,
    category: row.category,
    account: row.account,
    transaction_type: row.transaction_type
  })
  dialogVisible.value = true
}
async function submitForm() {
  await formRef.value.validate()
  const payload = {
    date: form.date,
    amount: form.amount,
    description: form.description,
    category: form.category,
    account: form.account,
    transaction_type: form.transaction_type
  }
  try {
    if (form.id) await api.put(`/api/transactions/${form.id}/`, payload)
    else await api.post('/api/transactions/', payload)
    dialogVisible.value = false
    await fetchList()
    ElMessage.success('保存成功')
  } catch { ElMessage.error('保存失败') }
}
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除该交易记录？`, '提示', { type: 'warning' })
    await api.delete(`/api/transactions/${row.id}/`)
    await fetchList()
    ElMessage.success('删除成功')
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

onMounted(async () => {
  await Promise.all([fetchMaster(), fetchList()])
})
</script>

<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span>交易记录</span>
        <div style="display:flex;gap:8px;">
          <el-button @click="resetFilters">重置筛选</el-button>
          <el-button type="primary" @click="openCreate">新增</el-button>
        </div>
      </div>
    </template>

    <div style="margin-bottom:12px; display:grid; grid-template-columns: 220px 160px 180px 220px 1fr 160px; gap:8px;">
      <el-date-picker v-model="filters.dateRange" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" />
      <el-select v-model="filters.type" placeholder="类型">
        <el-option label="全部" value="" />
        <el-option label="收入" value="income" />
        <el-option label="支出" value="expense" />
      </el-select>
      <el-select v-model="filters.account" placeholder="账户">
        <el-option label="全部" value="" />
        <el-option v-for="a in accounts" :key="a.id" :label="a.name" :value="String(a.id)" />
      </el-select>
      <el-select v-model="filters.category" placeholder="分类">
        <el-option label="全部" value="" />
        <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="String(c.id)" />
      </el-select>
      <el-input v-model="filters.keyword" placeholder="备注关键词" />
      <el-select v-model="filters.sort" placeholder="排序">
        <el-option label="按日期降序" value="-date" />
        <el-option label="按日期升序" value="date" />
        <el-option label="按金额降序" value="-amount" />
        <el-option label="按金额升序" value="amount" />
      </el-select>
    </div>

    <el-table :data="filtered" v-loading="loading" style="width:100%">
      <el-table-column prop="date" label="日期" width="120" />
      <el-table-column prop="amount" label="金额" width="120" />
      <el-table-column label="类型" width="120">
        <template #default="{ row }">
          <el-tag :type="row.transaction_type === 'income' ? 'success' : 'danger'">
            {{ row.transaction_type === 'income' ? '收入' : '支出' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="账户" min-width="140">
        <template #default="{ row }">
          {{ (accounts.find(a => a.id === row.account) || {}).name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="分类" min-width="140">
        <template #default="{ row }">
          {{ (categories.find(c => c.id === row.category) || {}).name || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="description" label="备注" min-width="220" show-overflow-tooltip />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-form-item label="日期" prop="date">
        <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" />
      </el-form-item>
      <el-form-item label="金额" prop="amount">
        <el-input v-model.number="form.amount" type="number" />
      </el-form-item>
      <el-form-item label="类型" prop="transaction_type">
        <el-radio-group v-model="form.transaction_type">
          <el-radio-button label="income">收入</el-radio-button>
          <el-radio-button label="expense">支出</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="账户" prop="account">
        <el-select v-model="form.account" placeholder="请选择账户">
          <el-option v-for="a in accounts" :key="a.id" :label="a.name" :value="a.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="分类" prop="category">
        <el-select v-model="form.category" placeholder="请选择分类">
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
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