<template>
  <div class="page-container" v-loading="loading">
    <el-breadcrumb separator="/" class="mb-16">
      <el-breadcrumb-item :to="{ name: 'home' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>{{ product?.category_name || '商品详情' }}</el-breadcrumb-item>
      <el-breadcrumb-item>{{ product?.name }}</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card v-if="product" shadow="never">
      <div class="detail-top">
        <div class="gallery">
          <el-image :src="product.main_image" fit="cover" class="main-image">
            <template #error>
              <div class="thumb-fallback main-fallback">
                <span>{{ product.name.slice(0, 2) }}</span>
              </div>
            </template>
          </el-image>
        </div>

        <div class="info">
          <h1 class="name">{{ product.name }}</h1>
          <p class="subtitle">{{ product.subtitle }}</p>

          <div class="price-panel">
            <div class="price-row">
              <span class="text-muted">售价</span>
              <span class="price price-large">{{ yuan(product.price) }}</span>
              <span v-if="Number(product.original_price) > Number(product.price)" class="origin">
                {{ yuan(product.original_price) }}
              </span>
            </div>
            <div class="meta-row">
              <span>库存 <b>{{ product.stock }}</b> {{ product.unit }}</span>
              <el-divider direction="vertical" />
              <span>累计销量 <b>{{ product.sales }}</b></span>
              <el-divider direction="vertical" />
              <span>分类 <b>{{ product.category_name }}</b></span>
            </div>
          </div>

          <div class="buy-row">
            <span class="text-muted">数量</span>
            <el-input-number v-model="quantity" :min="1" :max="Math.max(product.stock, 1)" />
          </div>

          <div class="action-row">
            <el-button
              type="primary"
              size="large"
              :disabled="!onSale || product.stock <= 0"
              :loading="adding"
              @click="onAddToCart"
            >
              加入购物车
            </el-button>
            <el-button
              type="danger"
              size="large"
              :disabled="!onSale || product.stock <= 0"
              @click="onBuyNow"
            >
              立即购买
            </el-button>
          </div>

          <el-alert v-if="!onSale" type="warning" :closable="false" show-icon title="该商品已下架，无法购买" />
          <el-alert
            v-else-if="product.stock <= 0"
            type="info"
            :closable="false"
            show-icon
            title="该商品暂时缺货，可先收藏或看看同类商品"
          />
        </div>
      </div>

      <el-tabs class="detail-tabs" model-value="detail">
        <el-tab-pane label="图文详情" name="detail">
          <div v-if="detailText" class="rich-text">{{ detailText }}</div>
          <el-empty v-else description="暂无图文详情" :image-size="80" />
        </el-tab-pane>
        <el-tab-pane label="规格参数" name="spec">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="商品编号">{{ product.id }}</el-descriptions-item>
            <el-descriptions-item label="所属分类">{{ product.category_name }}</el-descriptions-item>
            <el-descriptions-item label="计量单位">{{ product.unit }}</el-descriptions-item>
            <el-descriptions-item label="当前状态">
              {{ product.status === 1 ? '在售' : '已下架' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-empty v-else-if="!loading" description="商品不存在或已被删除" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { fetchProduct } from '@/api/catalog'
import { useCartStore } from '@/stores/cart'
import { useUserStore } from '@/stores/user'
import { plainText, yuan } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const user = useUserStore()
const cart = useCartStore()

const product = ref(null)
const loading = ref(false)
const adding = ref(false)
const quantity = ref(1)

const onSale = computed(() => product.value?.status === 1)
const detailText = computed(() => plainText(product.value?.detail))

async function load() {
  loading.value = true
  quantity.value = 1
  try {
    product.value = await fetchProduct(route.params.id)
  } catch {
    product.value = null
  } finally {
    loading.value = false
  }
}

function requireLogin() {
  if (user.isLoggedIn) return true
  ElMessage.warning('请先登录')
  router.push({ name: 'login', query: { redirect: route.fullPath } })
  return false
}

async function onAddToCart() {
  if (!requireLogin()) return
  adding.value = true
  try {
    await cart.add(product.value.id, quantity.value)
    ElMessage.success(`已加入购物车 ${quantity.value} ${product.value.unit}`)
  } catch {
    // 库存不足等提示由拦截器给出
  } finally {
    adding.value = false
  }
}

function onBuyNow() {
  if (!requireLogin()) return
  router.push({
    name: 'checkout',
    query: { buy: `${product.value.id}:${quantity.value}` },
  })
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<style scoped>
.detail-top {
  display: flex;
  gap: 32px;
  flex-wrap: wrap;
}

.gallery {
  width: 360px;
  max-width: 100%;
}

.main-image,
.main-fallback {
  width: 360px;
  height: 360px;
  max-width: 100%;
  border-radius: 6px;
}

.main-fallback {
  font-size: 22px;
}

.info {
  flex: 1;
  min-width: 280px;
}

.name {
  margin: 0 0 6px;
  font-size: 22px;
  line-height: 1.35;
}

.subtitle {
  margin: 0 0 14px;
  color: #e6a23c;
  font-size: 13px;
}

.price-panel {
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 14px 16px;
  margin-bottom: 18px;
}

.price-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 8px;
}

.origin {
  color: #c0c4cc;
  text-decoration: line-through;
  font-size: 13px;
}

.meta-row {
  font-size: 13px;
  color: #606266;
}

.buy-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.action-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.detail-tabs {
  margin-top: 28px;
}

.rich-text {
  color: #606266;
  line-height: 1.8;
}
</style>
