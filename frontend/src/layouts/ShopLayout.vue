<template>
  <div class="shop-shell">
    <header class="shop-header">
      <div class="header-inner">
        <router-link :to="{ name: 'home' }" class="logo">
          <el-icon :size="22"><Shop /></el-icon>
          <span>B2C 商城</span>
        </router-link>

        <div class="search-box">
          <el-input
            v-model="keyword"
            placeholder="搜索商品名称或卖点"
            clearable
            @keyup.enter="onSearch"
            @clear="onSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="onSearch">搜索</el-button>
            </template>
          </el-input>
        </div>

        <nav class="header-nav">
          <router-link :to="{ name: 'home' }">首页</router-link>
          <router-link :to="{ name: 'orders' }">我的订单</router-link>
          <router-link :to="{ name: 'cart' }" class="cart-link">
            <el-badge :value="cart.badge" :hidden="!cart.totalQuantity" type="danger">
              <el-icon :size="18"><ShoppingCart /></el-icon>
            </el-badge>
            <span>购物车</span>
          </router-link>
          <router-link v-if="user.isAdmin" :to="{ name: 'admin-categories' }">管理后台</router-link>

          <template v-if="user.isLoggedIn">
            <el-dropdown trigger="click">
              <span class="user-entry">
                <el-icon><UserFilled /></el-icon>
                {{ user.displayName }}
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="router.push({ name: 'profile' })">个人资料</el-dropdown-item>
                  <el-dropdown-item divided @click="onLogout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <router-link v-else :to="{ name: 'login' }">登录 / 注册</router-link>
        </nav>
      </div>
    </header>

    <main class="shop-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDown, Search, Shop, ShoppingCart, UserFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { useCartStore } from '@/stores/cart'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const user = useUserStore()
const cart = useCartStore()

const keyword = ref(route.query.keyword ?? '')

function onSearch() {
  router.push({ name: 'home', query: keyword.value ? { keyword: keyword.value } : {} })
}

function onLogout() {
  user.logout()
  ElMessage.success('已退出登录')
  router.push({ name: 'login' })
}

onMounted(() => {
  // 从首页搜索框跳到详情页再返回时，保持关键词与地址栏一致
  if (route.query.keyword) keyword.value = String(route.query.keyword)
})

watch(
  () => route.query.keyword,
  (value) => {
    keyword.value = value ?? ''
  },
)
</script>

<style scoped>
.shop-shell {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.shop-header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-inner {
  max-width: var(--page-max-width);
  margin: 0 auto;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 24px;
  /* 窄屏时让导航整行换到下方，避免用户名被裁切或压成竖排 */
  flex-wrap: wrap;
}

.logo {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 19px;
  font-weight: 700;
  color: var(--brand-color);
  text-decoration: none;
  white-space: nowrap;
}

.search-box {
  flex: 1 1 240px;
  min-width: 180px;
  max-width: 420px;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-left: auto;
  flex-wrap: wrap;
  white-space: nowrap;
}

.header-nav a {
  color: #606266;
  text-decoration: none;
  font-size: 14px;
  white-space: nowrap;
}

.header-nav a:hover,
.header-nav a.router-link-active {
  color: var(--brand-color);
}

.cart-link {
  display: flex;
  align-items: center;
  gap: 6px;
}

.user-entry {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
  outline: none;
}

.shop-main {
  flex: 1;
}
</style>
