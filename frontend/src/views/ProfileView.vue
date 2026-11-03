<template>
  <div class="page-container">
    <h2 class="page-title">个人资料</h2>

    <el-row :gutter="16">
      <el-col :xs="24" :md="14">
        <el-card shadow="never" v-loading="!user.profile">
          <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
            <el-form-item label="登录名">
              <el-input :model-value="user.profile?.username" disabled />
              <span class="text-muted">登录名注册后不可修改</span>
            </el-form-item>
            <el-form-item label="昵称" prop="nickname">
              <el-input v-model="form.nickname" maxlength="32" show-word-limit />
            </el-form-item>
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="form.phone" maxlength="20" placeholder="纯数字" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" maxlength="128" />
            </el-form-item>
            <el-form-item label="头像地址" prop="avatar">
              <el-input v-model="form.avatar" maxlength="255" placeholder="图片 URL，选填" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="onSave">保存修改</el-button>
              <el-button @click="reload">放弃修改</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="10">
        <el-card shadow="never" class="account-card">
          <template #header><span class="card-title">账号信息</span></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户 ID">{{ user.profile?.id }}</el-descriptions-item>
            <el-descriptions-item label="角色">
              <el-tag :type="user.isAdmin ? 'warning' : 'info'" size="small" effect="plain">
                {{ user.isAdmin ? '管理员' : '普通用户' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="账号状态">
              {{ user.profile?.status === 1 ? '正常' : '已禁用' }}
            </el-descriptions-item>
            <el-descriptions-item label="注册时间">{{ dateTime(user.profile?.created_at) }}</el-descriptions-item>
          </el-descriptions>
          <el-button class="logout-btn" type="danger" plain @click="onLogout">退出登录</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useUserStore } from '@/stores/user'
import { dateTime } from '@/utils/format'

const router = useRouter()
const user = useUserStore()

const formRef = ref()
const saving = ref(false)
const form = reactive({ nickname: '', phone: '', email: '', avatar: '' })

const rules = {
  nickname: [{ max: 32, message: '昵称不超过 32 位', trigger: 'blur' }],
  phone: [{ pattern: /^\d*$/, message: '手机号只能是数字', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
}

function reload() {
  const profile = user.profile
  if (!profile) return
  form.nickname = profile.nickname ?? ''
  form.phone = profile.phone ?? ''
  form.email = profile.email ?? ''
  form.avatar = profile.avatar ?? ''
}

async function onSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await user.saveProfile({ ...form })
    ElMessage.success('资料已更新')
  } catch {
    // 提示由拦截器给出
  } finally {
    saving.value = false
  }
}

function onLogout() {
  user.logout()
  ElMessage.success('已退出登录')
  router.push({ name: 'login' })
}

onMounted(async () => {
  if (!user.profile) {
    await user.loadProfile().catch(() => {})
  }
  reload()
})
</script>

<style scoped>
.page-title {
  margin: 0 0 16px;
  font-size: 20px;
}

.card-title {
  font-weight: 600;
}

.account-card {
  margin-bottom: 16px;
}

.logout-btn {
  width: 100%;
  margin-top: 16px;
}
</style>
