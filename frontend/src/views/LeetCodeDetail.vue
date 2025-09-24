<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../services/api'
import { ElMessage } from 'element-plus'
import { Document, Star, Tools } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const problem = ref({})

// 初始化 Markdown 解析器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true, // 支持换行
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return '<pre class="hljs"><code class="language-' + lang + '">' +
               hljs.highlight(str, { language: lang }).value +
               '</code></pre>';
      } catch (__) {}
    }
    // 如果没有指定语言，尝试自动检测
    try {
      const detected = hljs.highlightAuto(str)
      return '<pre class="hljs"><code class="language-' + detected.language + '">' +
             detected.value +
             '</code></pre>';
    } catch (__) {}
    return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>';
  }
})

// 计算属性：渲染后的 Markdown 内容
const renderedDescription = computed(() => {
  return problem.value.description ? md.render(problem.value.description) : ''
})

const renderedThinking = computed(() => {
  return problem.value.thinking ? md.render(problem.value.thinking) : ''
})

const renderedSolution = computed(() => {
  if (!problem.value.solution) return ''
  
  // 如果solution不是Markdown格式，直接包装成代码块
  const solution = problem.value.solution.trim()
  if (!solution.startsWith('```') && !solution.startsWith('<pre>')) {
    // 检测是否为代码（包含class、def、function等关键字）
    const isCode = /class\s+\w+|def\s+\w+|function\s+\w+|import\s+|from\s+|#include|public\s+class|private\s+|protected\s+|var\s+|let\s+|const\s+|int\s+|string\s+|void\s+/.test(solution)
    
    if (isCode) {
      // 自动包装成Python代码块
      return md.render('```python\n' + solution + '\n```')
    } else {
      // 普通文本，用pre标签包装
      return `<pre class="code-block">${md.utils.escapeHtml(solution)}</pre>`
    }
  }
  
  return md.render(solution)
})

async function fetchProblem() {
  loading.value = true
  try {
    const { data } = await api.get(`/api/leetcode/${route.params.id}/`)
    problem.value = data
  } catch (e) {
    ElMessage.error('加载失败')
    router.push({ name: 'leetcode' })
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push({ name: 'leetcode' })
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

async function toggleCompleted() {
  try {
    await api.patch(`/api/leetcode/${problem.value.id}/`, { completed: problem.value.completed })
    ElMessage.success('状态已更新')
  } catch (e) {
    problem.value.completed = !problem.value.completed
    ElMessage.error('更新失败')
  }
}

onMounted(fetchProblem)
</script>

<template>
  <div>
    <!-- 页面头部 -->
    <el-page-header @back="goBack" content="题目详情">

    </el-page-header>

    <el-card v-if="!loading" style="margin-top: 20px;">
      <!-- 题目标题和状态 -->
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">{{ problem.title }}</h1>
            <el-tag :type="getDifficultyColor(problem.difficulty)" size="large" effect="dark">
              {{ getDifficultyText(problem.difficulty) }}
            </el-tag>
          </div>
          <div style="display: flex; align-items: center; gap: 12px;">
            <span style="color: #666; font-size: 14px;">完成状态：</span>
            <el-switch 
              v-model="problem.completed" 
              active-text="已完成"
              inactive-text="未完成"
              @change="toggleCompleted"
            />
          </div>
        </div>
      </template>

      <!-- 题目描述 -->
      <el-card shadow="never" style="margin-bottom: 24px; border-left: 4px solid #409EFF;">
        <template #header>
          <div style="display: flex; align-items: center; gap: 8px;">
            <el-icon color="#409EFF"><Document /></el-icon>
            <h3 style="margin: 0; color: #409EFF; font-size: 18px;">题目描述</h3>
          </div>
        </template>
        <div 
          class="markdown-content" 
          v-html="renderedDescription"
          style="line-height: 1.6; font-size: 14px;"
        ></div>
      </el-card>

      <!-- 解题思路和解题方法 -->
      <el-row :gutter="24">
        <el-col :xs="24" :sm="24" :md="12" :lg="12">
          <el-card shadow="never" style="margin-bottom: 24px; border-left: 4px solid #67C23A;">
            <template #header>
              <div style="display: flex; align-items: center; gap: 8px;">
                <el-icon color="#67C23A"><Star /></el-icon>
                <h3 style="margin: 0; color: #67C23A; font-size: 18px;">解题思路</h3>
              </div>
            </template>
            <div 
              class="markdown-content" 
              v-html="renderedThinking"
              style="line-height: 1.6; font-size: 14px;"
            ></div>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :sm="24" :md="12" :lg="12">
          <el-card shadow="never" style="margin-bottom: 24px; border-left: 4px solid #E6A23C;">
            <template #header>
              <div style="display: flex; align-items: center; gap: 8px;">
                <el-icon color="#E6A23C"><Tools /></el-icon>
                <h3 style="margin: 0; color: #E6A23C; font-size: 18px;">解题方法</h3>
              </div>
            </template>
            <div 
              class="markdown-content" 
              v-html="renderedSolution"
              style="line-height: 1.6; font-size: 14px;"
            ></div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <el-skeleton v-else :rows="10" animated />
  </div>
</template>

<style scoped>
.markdown-content {
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.markdown-content :deep(pre) {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.4;
  margin: 16px 0;
  position: relative;
}

.markdown-content :deep(pre.hljs) {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.4;
  margin: 16px 0;
}

.markdown-content :deep(code) {
  background: #f1f3f4;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

.markdown-content :deep(pre code) {
  background: transparent;
  padding: 0;
  border-radius: 0;
  font-size: 13px;
  line-height: 1.4;
}

.markdown-content :deep(.code-block) {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.4;
  margin: 16px 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-content :deep(h1) {
  font-size: 2em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-content :deep(h2) {
  font-size: 1.5em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-content :deep(h3) {
  font-size: 1.25em;
}

.markdown-content :deep(p) {
  margin-bottom: 16px;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin-bottom: 16px;
  padding-left: 2em;
}

.markdown-content :deep(li) {
  margin-bottom: 4px;
}

.markdown-content :deep(blockquote) {
  margin: 16px 0;
  padding: 0 16px;
  color: #6a737d;
  border-left: 4px solid #dfe2e5;
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  margin: 16px 0;
  width: 100%;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #dfe2e5;
  padding: 8px 12px;
  text-align: left;
}

.markdown-content :deep(th) {
  background: #f6f8fa;
  font-weight: 600;
}

.markdown-content :deep(a) {
  color: #0366d6;
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .markdown-content :deep(pre) {
    font-size: 12px;
    padding: 12px;
  }
  
  .markdown-content :deep(code) {
    font-size: 12px;
  }
  
  .markdown-content :deep(.code-block) {
    font-size: 12px;
    padding: 12px;
  }
}
</style>
