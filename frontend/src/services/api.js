import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000', // 确保与后端启动端口一致
  timeout: 10000,
})

let isRefreshing = false
let pendingQueue = []

function onRefreshed(newAccess) {
  pendingQueue.forEach(cb => cb(newAccess))
  pendingQueue = []
}

api.interceptors.request.use(config => {
  const access = localStorage.getItem('access')
  if (access) {
    config.headers.Authorization = `Bearer ${access}`
  }
  return config
})

api.interceptors.response.use(
  res => res,
  async err => {
    const { response, config } = err
    if (!response) throw err

    if (response.status === 401 && !config.__isRetryRequest) {
      const refresh = localStorage.getItem('refresh')
      if (!refresh) {
        // 无刷新令牌，直接失败
        throw err
      }

      // 单航道刷新，避免并发重复刷新
      if (!isRefreshing) {
        isRefreshing = true
        try {
          const { data } = await axios.post('http://127.0.0.1:8000/api/refresh-token/', { refresh })
          const newAccess = data.access
          localStorage.setItem('access', newAccess)
          isRefreshing = false
          onRefreshed(newAccess)
        } catch (e) {
          isRefreshing = false
          pendingQueue = []
          // 刷新失败，清空本地并抛出
          localStorage.removeItem('access')
          localStorage.removeItem('refresh')
          localStorage.removeItem('user')
          throw e
        }
      }

      // 挂起当前请求，等待刷新完成后重试
      return new Promise(resolve => {
        pendingQueue.push(newAccess => {
          config.headers.Authorization = `Bearer ${newAccess}`
          config.__isRetryRequest = true
          resolve(api(config))
        })
      })
    }

    throw err
  }
)

export default api
