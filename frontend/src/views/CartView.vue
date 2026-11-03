<template>
  <div class="page-container">
    <h2 class="page-title">购物车</h2>

    <el-card shadow="never" v-loading="cart.loading">
      <el-empty v-if="!cart.items.length" description="购物车还是空的">
        <el-button type="primary" @click="router.push({ name: 'home' })">去挑点东西</el-button>
      </el-empty>

      <template v-else>
        <el-table :data="cart.items" style="width: 100%" empty-text="购物车为空">
          <el-table-column label="选择" width="64">
            <template #default="{ row }">
              <el-checkbox
                :model-value="row.checked === 1"
                :disabled="!row.on_sale"
                @change="(val) => onCheckChange(row, val)"
              />
            </template>
          </el-table-column>

          <el-table-column label="商品" min-width="280">
            <template #default="{ row }">
              <div class="cart-product">
                <el-image :src="row.product_image" fit="cover" class="cart-thumb">
                  <template #error>
                    <div class="thumb-fallback cart-thumb">
                      <span>{{ row.product_name.slice(0, 2) }}</span>
                    </div>
                  </template>
                </el-image>
                <div class="cart-product-info">
                  <router-link :to="{ name: 'product-detail', params: { id: row.product_id } }" class="link">
                    {{ row.product_name }}
                  </router-link>
                  <div>
                    <el-tag v-if="!row.on_sale" type="danger" size="small" effect="plain">已下架</el-tag>
                    <span v-else class="text-muted">剩余库存 {{ row.stock }}</span>
                  </div>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="单价" width="110" align="right">
            <template #default="{ row }">
              <span class="price">{{ yuan(row.price) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="数量" width="170" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.quantity"
                :min="1"
                :max="Math.max(row.stock, 1)"
                size="small"
                :disabled="!row.on_sale"
                @change="(val, old) => onQuantityChange(row, val, old)"
              />
            </template>
          </el-table-column>

          <el-table-column label="小计" width="120" align="right">
            <template #default="{ row }">
              <span class="price">{{ yuan(row.subtotal) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="90" align="center">
            <template #default="{ row }">
              <el-button text type="danger" size="small" @click="onRemove(row)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="cart-footer">
          <div class="footer-left">
            <el-button text type="danger" @click="onClear">清空购物车</el-button>
            <span class="text-muted">已选 {{ cart.checkedCount }} 种 / {{ cart.totalQuantity }} 件</span>
          </div>
          <div class="footer-right">
            <span class="text-muted">合计（不含运费）：</span>
            <span class="price price-large">{{ yuan(cart.totalAmount) }}</span>
            <el-button
              type="primary"
              size="large"
              :disabled="!cart.checkedCount"
              @click="router.push({ name: 'checkout' })"
            >
              去结算
            </el-button>
          </div>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { useCartStore } from '@/stores/cart'
import { yuan } from '@/utils/format'

const router = useRouter()
const cart = useCartStore()

onMounted(() => cart.refresh())

// 后端会重算整单金额，所以每次改动都拿最新购物车覆盖本地
async function onCheckChange(row, checked) {
  await cart.updateItem(row.id, { checked: checked ? 1 : 0 }).catch(() => row.checked === 1)
}

async function onQuantityChange(row, value, oldValue) {
  if (value === oldValue) return
  await cart.updateItem(row.id, { quantity: value }).catch(() => {
    row.quantity = oldValue
  })
}

async function onRemove(row) {
  await ElMessageBox.confirm(`确定把「${row.product_name}」移出购物车吗？`, '移除确认', {
    type: 'warning',
    confirmButtonText: '移除',
    cancelButtonText: '再想想',
  }).catch(() => Promise.reject('cancel'))
  await cart.removeItem(row.id)
  ElMessage.success('已移出购物车')
}

async function onClear() {
  await ElMessageBox.confirm('确定清空整个购物车吗？', '清空确认', {
    type: 'warning',
    confirmButtonText: '清空',
    cancelButtonText: '取消',
  }).catch(() => Promise.reject('cancel'))
  await cart.clear()
  ElMessage.success('购物车已清空')
}
</script>

<style scoped>
.page-title {
  margin: 0 0 16px;
  font-size: 20px;
}

.cart-product {
  display: flex;
  gap: 12px;
  align-items: center;
}

.cart-thumb {
  width: 64px;
  height: 64px;
  flex: none;
}

.cart-product-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.link {
  color: #303133;
  text-decoration: none;
}

.link:hover {
  color: var(--brand-color);
}

.cart-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
  flex-wrap: wrap;
  gap: 12px;
}

.footer-left,
.footer-right {
  display: flex;
  align-items: center;
  gap: 14px;
}
</style>
