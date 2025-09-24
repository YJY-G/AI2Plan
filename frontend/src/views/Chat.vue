<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../services/api'

// 新增：Markdown 渲染
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'
// 可选高亮
// import hljs from 'highlight.js'
// import 'highlight.js/styles/github.css'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  // 可选高亮，若启用请取消注释并安装 highlight.js
  // highlight: function (str, lang) {
  //   if (lang && hljs.getLanguage(lang)) {
  //     try {
  //       return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`
  //     } catch (_) {}
  //   }
  //   return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  // }
})

function render(msg) {
  if (!msg) return ''
  const role = msg.role || msg.type
  const content = typeof msg === 'string' ? msg : (msg.content || msg.text || '')
  // 人类消息当纯文本，AI 消息按 Markdown 渲染
  if (role === 'ai') {
    const html = md.render(content)
    return DOMPurify.sanitize(html)
  } else {
    const html = md.utils.escapeHtml(content).replace(/\n/g, '<br/>')
    return DOMPurify.sanitize(html)
  }
}

// 下面保留你已有的逻辑
const route = useRoute()
const id = route.params.id

const loading = ref(false)
const sending = ref(false)
const session = ref(null)
const messages = ref([])
const input = ref('')

// 将 [["k","v"], ...] 转成对象；若已是对象则原样返回
function toObj(x) {
  if (Array.isArray(x)) {
    try {
      return Object.fromEntries(x)
    } catch {
      return {}
    }
  }
  return x && typeof x === 'object' ? x : {}
}

// 规范化 memory：只保留 human / ai，按顺序输出 { role, content }
function normalizeMemory(memory) {
  if (!Array.isArray(memory)) return []
  const out = []
  for (const item of memory) {
    const obj = toObj(item)
    const t = obj.type || obj.role
    const c = obj.content || obj.text
    if ((t === 'human' || t === 'ai') && typeof c === 'string') {
      out.push({ role: t, content: c })
    }
  }
  return out
}

function extractText(msg) {
  if (!msg) return ''
  if (typeof msg === 'string') return msg
  return msg.content || msg.text || ''
}
function extractRole(msg) {
  if (!msg) return 'unknown'
  return msg.role || msg.type || 'unknown'
}

async function loadDetail() {
  loading.value = true
  try {
    const { data } = await api.get(`/api/histories/${id}/`)
    session.value = data
    messages.value = normalizeMemory(data.memory)
  } finally {
    loading.value = false
  }
}



async function sendMessage() {
  const text = input.value.trim()
  if (!text || !session.value?.session_id) return
  sending.value = true
  try {
    messages.value.push({ role: 'human', content: text })
    input.value = ''
    const { data } = await api.post('/api/chat/', {
      message: text,
      session_id: session.value.session_id,
    }, { timeout: 180000 })
    if (data?.success) {
      messages.value.push({ role: 'ai', content: data.response })
    } else {
      messages.value.push({ role: 'system', content: data?.error || '发送失败' })
    }
  } catch (e) {
    messages.value.push({ role: 'system', content: '网络或服务异常' })
  } finally {
    sending.value = false
  }
}

onMounted(loadDetail)
</script>

<template>
  <div style="display:flex;flex-direction:column;height:100%;">
    <div style="margin-bottom:8px;">
      <el-tag type="success" v-if="session?.session_id">会话：{{ session.session_id }}</el-tag>
    </div>

    <div style="flex:1;overflow:auto;border:1px solid var(--el-border-color);border-radius:6px;padding:12px;">
      <div v-if="loading">加载中...</div>
      <div v-else>
        <div v-for="(m, idx) in messages" :key="idx" style="margin-bottom:12px;">
          <div style="font-size:12px;color:#909399;margin-bottom:2px;">{{ (m.role || m.type) }}</div>
          <div style="white-space:normal;" v-html="render(m)"></div>
        </div>
        <div v-if="!messages.length && !loading" style="color:#909399;">暂无历史消息</div>
      </div>
    </div>

    <div style="display:flex;gap:8px;margin-top:12px;">
      <el-input
        v-model="input"
        type="textarea"
        :rows="2"
        placeholder="输入你的消息..."
        @keydown.enter.prevent="sendMessage"
      />
      <el-button type="primary" :loading="sending" @click="sendMessage">发送</el-button>
    </div>
  </div>
</template>

<style scoped>
/* 让 Markdown 段落更易读 */
:deep(pre) {
  background: #f6f8fa;
  padding: 10px 12px;
  border-radius: 6px;
  overflow: auto;
}
:deep(code) {
  background: #f6f8fa;
  padding: 2px 4px;
  border-radius: 4px;
}
:deep(a) {
  color: #409EFF;
  text-decoration: none;
}
</style>
