<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const form = reactive({
  username: '',
  password: ''
})
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const onSubmit = async () => {
  errorMsg.value = ''
  successMsg.value = ''
  loading.value = true
  try {
    await auth.register({ username: form.username, password: form.password })
    successMsg.value = '注册成功，已自动登录'
    setTimeout(() => router.replace({ name: 'todos' }), 600)
  } catch (e) {
    errorMsg.value = '注册失败，用户名可能已存在'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-row justify="center" style="margin-top: 120px;">
    <el-col :span="8">
      <el-card>
        <h2 style="margin-bottom: 20px;">注册</h2>
        <el-form @submit.prevent="onSubmit" label-width="80px">
          <el-form-item label="用户名">
            <el-input v-model="form.username" placeholder="输入用户名" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" placeholder="输入密码" show-password type="password" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" @click="onSubmit">注册</el-button>
            <el-button link @click="$router.push({ name: 'login' })">去登录</el-button>
          </el-form-item>
          <el-alert v-if="errorMsg" type="error" :closable="false" :title="errorMsg" />
          <el-alert v-if="successMsg" type="success" :closable="false" :title="successMsg" />
        </el-form>
      </el-card>
    </el-col>
  </el-row>
</template>
