<template>
  <el-card class="product-card" shadow="hover" :body-style="{ padding: '12px', overflow: 'hidden' }">
    <div class="thumb-wrap" @click="goDetail">
      <el-image :src="product.main_image" fit="cover" class="product-thumb">
        <template #error>
          <div class="thumb-fallback">
            <span>{{ product.name.slice(0, 2) }}</span>
          </div>
        </template>
      </el-image>
      <el-tag v-if="product.stock <= 0" class="stock-tag" type="danger" size="small" effect="dark">
        已售罄
      </el-tag>
    </div>

    <h3 class="product-name" :title="product.name">{{ product.name }}</h3>
    <p class="product-subtitle">{{ product.subtitle || product.category_name || '—' }}</p>

    <div class="product-price-row">
      <span class="price price-large">{{ yuan(product.price) }}</span>
      <span v-if="Number(product.original_price) > Number(product.price)" class="origin-price">
        {{ yuan(product.original_price) }}
      </span>
    </div>

    <div class="product-meta">
      <span class="text-muted">库存 {{ product.stock }} {{ product.unit }}</span>
      <span class="text-muted">已售 {{ product.sales }}</span>
    </div>

    <div class="product-actions">
      <el-button size="small" @click="goDetail">详情</el-button>
      <el-button
        size="small"
        type="primary"
        :disabled="product.stock <= 0"
        :loading="adding"
        @click="onAddToCart"
      >
        加入购物车
      </el-button>
    </div>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useCartStore } from '@/stores/cart'
import { useUserStore } from '@/stores/user'
import { yuan } from '@/utils/format'

const props = defineProps({
  product: { type: Object, required: true },
})

const router = useRouter()
const user = useUserStore()
const cart = useCartStore()
const adding = ref(false)

function goDetail() {
  router.push({ name: 'product-detail', params: { id: props.product.id } })
}

async function onAddToCart() {
  if (!user.isLoggedIn) {
    ElMessage.warning('请先登录后再加购')
    router.push({ name: 'login', query: { redirect: router.currentRoute.value.fullPath } })
    return
  }
  adding.value = true
  try {
    await cart.add(props.product.id, 1)
    ElMessage.success('已加入购物车')
  } catch {
    // 库存不足/已下架等提示由拦截器给出
  } finally {
    adding.value = false
  }
}
</script>

<style scoped>
.product-card {
  height: 100%;
}

.thumb-wrap {
  position: relative;
  cursor: pointer;
}

.stock-tag {
  position: absolute;
  top: 8px;
  right: 8px;
}

.product-name {
  margin: 10px 0 4px;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  height: 40px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.product-subtitle {
  margin: 0 0 6px;
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-price-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  /* 划线价在窄卡里换到第二行，而不是把整行撑出横向滚动条 */
  flex-wrap: wrap;
}

.origin-price {
  font-size: 12px;
  color: #c0c4cc;
  text-decoration: line-through;
}

.product-meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  margin: 6px 0 10px;
}

.product-actions {
  display: flex;
  gap: 8px;
}

.product-actions .el-button {
  /* min-width: 0 才能让 flex 收缩按钮，否则按钮内容宽度就是下限 */
  flex: 1 1 auto;
  min-width: 0;
  margin-left: 0;
}

.product-actions :deep(.el-button > span) {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
