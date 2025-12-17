import axios from 'axios'

const service = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 5000
})

// 登录接口
function login(username, password) {
  return service.post('/player/login', null, {
    params: { username, password }
  }).then(res => res.data)
}

// 注册接口
function register(username, password) {
  return service.post('/player/register', null, {
    params: { username, password }
  }).then(res => res.data)
}

// 导出为 Vue 插件方便挂载
export default {
  install(app) {
    app.config.globalProperties.$api = { login, register }
  }
}
