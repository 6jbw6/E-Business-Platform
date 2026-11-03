import axios from 'axios'
import { ElMessage } from 'element-plus'

export const TOKEN_KEY = 'mall_access_token'

/** 后端统一响应体里的业务码非 0，或 HTTP 4xx/5xx，都会抛出这个错误。 */
export class ApiError extends Error {
  constructor(message, code, status) {
    super(message || '请求失败')
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 登录态失效时由 App.vue 监听并跳转，避免这里反向依赖 router/store 形成循环引用
const onUnauthorized = () => window.dispatchEvent(new Event('mall:auth-expired'))

http.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 0) {
        return body.data
      }
      return Promise.reject(new ApiError(body.message, body.code, response.status))
    }
    return body
  },
  (error) => {
    const silent = error.config?.silent === true
    const payload = error.response?.data
    let apiError

    if (error.response) {
      apiError = new ApiError(
        payload?.message || `请求失败（HTTP ${error.response.status}）`,
        payload?.code,
        error.response.status,
      )
    } else {
      apiError = new ApiError(
        error.code === 'ECONNABORTED' ? '请求超时，请检查后端服务是否在运行' : '无法连接后端服务，请确认 8000 端口已启动',
        undefined,
        0,
      )
    }

    if (apiError.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      onUnauthorized()
      if (!silent) ElMessage.warning(apiError.message)
    } else if (!silent) {
      ElMessage.error(apiError.message)
    }

    return Promise.reject(apiError)
  },
)

export default http
