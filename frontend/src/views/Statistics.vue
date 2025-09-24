<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../services/api'
import dayjs from 'dayjs'

const tx = ref([])
const categories = ref([])

async function fetchAll() {
  const [{ data: t }, { data: c }] = await Promise.all([
    api.get('/api/transactions/'),
    api.get('/api/categories/')
  ])
  tx.value = Array.isArray(t) ? t : (t.results || [])
  categories.value = Array.isArray(c) ? c : (c.results || [])
}

const byMonth = computed(() => {
  const map = {}
  tx.value.forEach(item => {
    const ym = dayjs(item.date).format('YYYY-MM')
    map[ym] ||= { income: 0, expense: 0 }
    const amt = Number(item.amount)
    if (item.transaction_type === 'income') map[ym].income += amt
    else map[ym].expense += amt
  })
  const rows = Object.entries(map).map(([month, v]) => ({ month, ...v, net: v.income - v.expense }))
  rows.sort((a,b) => a.month.localeCompare(b.month))
  return rows
})

const byCategory = computed(() => {
  const cmap = {}
  tx.value.forEach(item => {
    if (item.transaction_type !== 'expense') return
    const name = (categories.value.find(c => c.id === item.category) || {}).name || '未分类'
    cmap[name] = (cmap[name] || 0) + Number(item.amount)
  })
  return Object.entries(cmap).map(([name, total]) => ({ name, total })).sort((a,b) => b.total - a.total)
})

onMounted(fetchAll)
</script>

<template>
  <el-card>
    <template #header>统计报表</template>

    <el-row :gutter="12">
      <el-col :span="12">
        <el-card>
          <template #header>按月统计</template>
          <el-table :data="byMonth" size="small">
            <el-table-column prop="month" label="月份" width="120" />
            <el-table-column prop="income" label="收入" />
            <el-table-column prop="expense" label="支出" />
            <el-table-column prop="net" label="净值" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>按分类支出</template>
          <el-table :data="byCategory" size="small">
            <el-table-column prop="name" label="分类" />
            <el-table-column prop="total" label="支出总额" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </el-card>
</template>
