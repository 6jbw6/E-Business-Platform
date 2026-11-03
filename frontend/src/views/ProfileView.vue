<template>
  <div class="page-container">
    <h2 class="page-title">个人资料</h2>

    <el-row :gutter="16">
      <el-col :xs="24" :md="14">
        <el-card shadow="never" v-loading="!user.profile">
          <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
            <el-form-item label="头像">
              <div class="avatar-pick" @click="pickImage" title="点击更换头像">
                <el-avatar :size="72" :src="user.profile?.avatar" shape="circle">
                  {{ user.displayName.slice(0, 1) }}
                </el-avatar>
                <div class="avatar-mask"><el-icon><Camera /></el-icon><span>更换</span></div>
              </div>
              <input
                ref="fileInputRef"
                type="file"
                accept="image/jpeg,image/png,image/gif,image/webp"
                class="hidden-input"
                @change="onFilePicked"
              />
            </el-form-item>
            <el-form-item label="登录名">
              <el-input :model-value="user.profile?.username" disabled />
            </el-form-item>
            <el-form-item label="昵称" prop="nickname">
              <el-input v-model="form.nickname" maxlength="32" @blur="autoSave('nickname')" />
            </el-form-item>
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="form.phone" maxlength="20" placeholder="纯数字" @blur="autoSave('phone')" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" maxlength="128" @blur="autoSave('email')" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="10">
        <el-card shadow="never" class="account-card">
          <template #header><span class="card-title">账号信息</span></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户 ID">{{ user.profile?.id }}</el-descriptions-item>
            <el-descriptions-item label="角色">{{ user.isAdmin ? '管理员' : '普通用户' }}</el-descriptions-item>
            <el-descriptions-item label="账号状态">
              {{ user.profile?.status === 1 ? '正常' : '已禁用' }}
            </el-descriptions-item>
            <el-descriptions-item label="注册时间">{{ dateTime(user.profile?.created_at) }}</el-descriptions-item>
          </el-descriptions>
          <el-button class="logout-btn" type="danger" plain @click="onLogout">退出登录</el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="cropVisible" title="裁剪圆形头像" width="560px" @closed="releaseObjectUrl">
      <div class="crop-wrap">
        <Cropper
          :src="cropSource"
          :stencil-component="CircleStencil"
          :stencil-props="{ aspectRatio: 1 }"
          class="cropper-box"
          @change="onCropChange"
        />
        <span class="text-muted crop-hint">拖动图片、缩放圆形选区，圆内的部分就是最终头像</span>
      </div>
      <template #footer>
        <el-button @click="cropVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" :disabled="!cropCanvas" @click="onConfirmCrop">
          上传头像
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Camera } from '@element-plus/icons-vue'
import { CircleStencil, Cropper } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'

import { useUserStore } from '@/stores/user'
import { dateTime } from '@/utils/format'

const MAX_PICK_BYTES = 5 * 1024 * 1024
const AVATAR_OUTPUT_SIZE = 256

const router = useRouter()
const user = useUserStore()

const formRef = ref()
const form = reactive({ nickname: '', phone: '', email: '' })

const fileInputRef = ref()
const cropVisible = ref(false)
const cropSource = ref('')
const cropCanvas = ref(null)
const uploading = ref(false)

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
}

function pickImage() {
  fileInputRef.value?.click()
}

function releaseObjectUrl() {
  if (cropSource.value) URL.revokeObjectURL(cropSource.value)
  cropSource.value = ''
  cropCanvas.value = null
}

function onFilePicked(event) {
  const input = event.target
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (file.size > MAX_PICK_BYTES) {
    ElMessage.warning(`图片太大（${(file.size / 1024 / 1024).toFixed(1)} MB），请选 5 MB 以内的`)
    return
  }
  releaseObjectUrl()
  cropSource.value = URL.createObjectURL(file)
  cropVisible.value = true
}

// 裁剪库在选区变化时给出已裁好的 canvas，直接拿它做导出源
function onCropChange({ canvas }) {
  cropCanvas.value = canvas ?? null
}

function toCircularPng(source) {
  return new Promise((resolve) => {
    const size = AVATAR_OUTPUT_SIZE
    const output = document.createElement('canvas')
    output.width = size
    output.height = size
    const ctx = output.getContext('2d')
    ctx.save()
    ctx.beginPath()
    ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2)
    ctx.clip()
    ctx.drawImage(source, 0, 0, size, size)
    ctx.restore()
    output.toBlob((blob) => resolve(blob), 'image/png')
  })
}

async function onConfirmCrop() {
  if (!cropCanvas.value) {
    ElMessage.warning('还没有可上传的裁剪结果')
    return
  }
  const blob = await toCircularPng(cropCanvas.value)
  if (!blob) {
    ElMessage.error('图片导出失败，请换一张试试')
    return
  }
  uploading.value = true
  try {
    await user.uploadAvatar(blob)
    ElMessage.success('头像已更新')
    cropVisible.value = false
  } catch {
    // 类型不合法、图片过大等提示由拦截器给出
  } finally {
    uploading.value = false
  }
}

// 失焦即保存：字段没变、或该字段校验没过，都不发请求
async function autoSave(field) {
  const value = form[field] ?? ''
  if (value === (user.profile?.[field] ?? '')) return

  const valid = await formRef.value?.validateField(field).then(() => true).catch(() => false)
  if (!valid) return

  try {
    await user.saveProfile({ [field]: value })
    ElMessage.success('已保存')
  } catch {
    // 提示由拦截器给出
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

.avatar-pick {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  cursor: pointer;
}

.avatar-pick .el-avatar {
  background: var(--brand-color);
  color: #fff;
}

/* 悬停才浮出「更换」遮罩，平时保持一张干净的圆头像 */
.avatar-mask {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}

.avatar-pick:hover .avatar-mask {
  opacity: 1;
}

.hidden-input {
  display: none;
}

.crop-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cropper-box {
  height: 340px;
  background: #f0f2f5;
}

.crop-hint {
  text-align: center;
}
</style>
