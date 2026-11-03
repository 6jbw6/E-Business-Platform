<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="login-title">B2C 商城</h1>
      <p class="login-subtitle">后端接口课程演示，登录后可使用购物车与下单</p>

      <el-tabs v-model="tab">
        <el-tab-pane label="登录" name="login">
          <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" label-position="top" @submit.prevent>
            <el-form-item label="登录名" prop="username">
              <el-input v-model="loginForm.username" placeholder="请输入登录名" :prefix-icon="User" @keyup.enter="onLogin" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="loginForm.password" type="password" show-password placeholder="请输入密码" :prefix-icon="Lock" @keyup.enter="onLogin" />
            </el-form-item>
            <el-button type="primary" class="submit-btn" :loading="submitting" @click="onLogin">登录</el-button>
          </el-form>

          <el-divider>演示账号（点击直接填入）</el-divider>
          <div class="quick-fill">
            <el-tag class="quick-tag" effect="plain" @click="fill('student01', 'Student@123')">普通用户 student01</el-tag>
            <el-tag class="quick-tag" type="warning" effect="plain" @click="fill('admin', 'Admin@123456')">管理员 admin</el-tag>
          </div>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" label-position="top" @submit.prevent>
            <el-form-item label="登录名" prop="username">
              <el-input v-model="registerForm.username" placeholder="4-32 位字母或数字" :prefix-icon="User" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="registerForm.password" type="password" show-password placeholder="至少 6 位" :prefix-icon="Lock" />
            </el-form-item>
            <el-form-item label="昵称" prop="nickname">
              <el-input v-model="registerForm.nickname" placeholder="选填，留空则用登录名" />
            </el-form-item>
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="registerForm.phone" placeholder="选填，纯数字" />
            </el-form-item>
            <el-button type="primary" class="submit-btn" :loading="submitting" @click="onRegister">注册并登录</el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'

import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const user = useUserStore()

const tab = ref('login')
const submitting = ref(false)
const loginFormRef = ref()
const registerFormRef = ref()

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', password: '', nickname: '', phone: '' })

const loginRules = {
  username: [{ required: true, message: '请输入登录名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerRules = {
  username: [
    { required: true, message: '请输入登录名', trigger: 'blur' },
    { min: 4, max: 32, message: '长度需在 4-32 位之间', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9]+$/, message: '只能由字母和数字组成', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 64, message: '长度需在 6-64 位之间', trigger: 'blur' },
  ],
  phone: [{ pattern: /^\d*$/, message: '手机号只能是数字', trigger: 'blur' }],
}

function fill(username, password) {
  tab.value = 'login'
  loginForm.username = username
  loginForm.password = password
}

function goAfterLogin() {
  const redirect = route.query.redirect
  router.replace(typeof redirect === 'string' ? redirect : { name: 'home' })
}

async function onLogin() {
  const valid = await loginFormRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const data = await user.login({ ...loginForm })
    ElMessage.success(`欢迎回来，${data.user.nickname || data.user.username}`)
    goAfterLogin()
  } catch {
    // 错误提示已由 axios 拦截器统一弹出
  } finally {
    submitting.value = false
  }
}

async function onRegister() {
  const valid = await registerFormRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const payload = { ...registerForm }
    if (!payload.nickname) delete payload.nickname
    if (!payload.phone) delete payload.phone
    await user.register(payload)
    await user.login({ username: registerForm.username, password: registerForm.password })
    ElMessage.success('注册成功，已自动登录')
    goAfterLogin()
  } catch {
    // 同上，拦截器已提示具体原因（如登录名已被注册）
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e02e24 0%, #f76b1d 100%);
  padding: 24px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 10px;
  padding: 28px 32px 32px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18);
}

.login-title {
  margin: 0;
  font-size: 24px;
  color: var(--brand-color);
}

.login-subtitle {
  margin: 6px 0 18px;
  font-size: 13px;
  color: #909399;
}

.submit-btn {
  width: 100%;
  margin-top: 4px;
}

.quick-fill {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.quick-tag {
  cursor: pointer;
}
</style>
