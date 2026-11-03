<template>
  <el-container class="admin-shell">
    <el-aside width="200px" class="admin-aside">
      <div class="aside-brand">
        <el-icon :size="18"><Platform /></el-icon>
        <span>商城管理后台</span>
      </div>
      <el-menu :default-active="route.name" router class="aside-menu">
        <el-menu-item :index="'admin-categories'" :route="{ name: 'admin-categories' }">
          <el-icon><Files /></el-icon>
          <span>分类管理</span>
        </el-menu-item>
        <el-menu-item :index="'admin-products'" :route="{ name: 'admin-products' }">
          <el-icon><Goods /></el-icon>
          <span>商品管理</span>
        </el-menu-item>
        <el-menu-item :index="'admin-orders'" :route="{ name: 'admin-orders' }">
          <el-icon><Van /></el-icon>
          <span>订单发货</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="admin-header">
        <span class="admin-title">{{ route.meta.title }}</span>
        <div class="admin-actions">
          <el-tag type="warning" effect="plain" size="small">管理员：{{ user.displayName }}</el-tag>
          <el-button text @click="router.push({ name: 'home' })">
            <el-icon><Back /></el-icon>
            返回商城首页
          </el-button>
          <el-button text type="danger" @click="onLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const user = useUserStore()

function onLogout() {
  user.logout()
  ElMessage.success('已退出登录')
  router.push({ name: 'login' })
}
</script>

<style scoped>
.admin-shell {
  min-height: 100vh;
}

.admin-aside {
  background: #263445;
  color: #fff;
}

.aside-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 60px;
  padding: 0 16px;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.aside-menu {
  border-right: none;
  background: transparent;
  --el-menu-bg-color: transparent;
  --el-menu-text-color: #c0c4cc;
  --el-menu-hover-bg-color: rgba(255, 255, 255, 0.08);
  --el-menu-active-color: #ffd04b;
}

.admin-header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  /* 空间不够时让操作区换到第二行，而不是把标题挤成竖排或省略号 */
  flex-wrap: wrap;
  height: auto;
  min-height: 60px;
  padding-top: 8px;
  padding-bottom: 8px;
}

.admin-title {
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.admin-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.admin-main {
  background: #f5f6f8;
}
</style>
