<template>
  <div class="page-container">
    <h2 class="page-title">确认订单</h2>

    <el-row :gutter="16">
      <el-col :xs="24" :md="15">
        <el-card shadow="never" class="mb-16">
          <template #header><span class="card-title">收货信息</span></template>
          <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
            <el-form-item label="收货人" prop="receiver_name">
              <el-input v-model="form.receiver_name" placeholder="请输入真实姓名" maxlength="32" show-word-limit />
            </el-form-item>
            <el-form-item label="联系电话" prop="receiver_phone">
              <el-input v-model="form.receiver_phone" placeholder="用于配送联系" maxlength="20" />
            </el-form-item>
            <el-form-item label="收货地址" prop="receiver_address">
              <el-input
                v-model="form.receiver_address"
                type="textarea"
                :rows="3"
                maxlength="255"
                show-word-limit
                placeholder="省 / 市 / 区 / 街道门牌号"
              />
            </el-form-item>
            <el-form-item label="买家备注">
              <el-input v-model="form.remark" maxlength="255" show-word-limit placeholder="选填，例如工作日送达" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never">
          <template #header>
            <span class="card-title">商品清单</span>
            <el-tag v-if="isDirectBuy" class="head-tag" type="warning" size="small" effect="plain">直接购买</el-tag>
            <el-tag v-else class="head-tag" size="small" effect="plain">来自购物车勾选</el-tag>
          </template>

          <el-table :data="lines" empty-text="没有可结算的商品">
            <el-table-column label="商品" min-width="240">
              <template #default="{ row }">
                <div class="line-name">
                  <el-image :src="row.image" fit="cover" class="line-thumb">
                    <template #error>
                      <div class="thumb-fallback line-thumb"><span>{{ row.name.slice(0, 2) }}</span></div>
                    </template>
                  </el-image>
                  <span>{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="单价" width="110" align="right">
              <template #default="{ row }">{{ yuan(row.price) }}</template>
            </el-table-column>
            <el-table-column label="数量" width="90" align="center">
              <template #default="{ row }">{{ row.quantity }}</template>
            </el-table-column>
            <el-table-column label="小计" width="120" align="right">
              <template #default="{ row }">
                <span class="price">{{ yuan(row.subtotal) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="9">
        <el-card shadow="never" class="summary-card">
          <template #header><span class="card-title">费用合计</span></template>
          <div class="summary-row">
            <span>商品总额</span>
            <span>{{ yuan(totalAmount) }}</span>
          </div>
          <div class="summary-row">
            <span>运费</span>
            <span>{{ yuan(freight) }}</span>
          </div>
          <p class="freight-tip">满 99 元包邮，不足收 10 元运费；最终以提交结果为准。</p>
          <el-divider />
          <div class="summary-row total">
            <span>应付金额</span>
            <span class="price price-large">{{ yuan(payAmount) }}</span>
          </div>
          <el-button
            type="danger"
            size="large"
            class="submit-btn"
            :loading="submitting"
            :disabled="!lines.length"
            @click="onSubmit"
          >
            提交订单
          </el-button>
          <el-button text class="back-btn" @click="router.back()">返回继续购物</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { fetchProduct } from '@/api/catalog'
import { createOrder } from '@/api/orders'
import { useCartStore } from '@/stores/cart'
import { yuan } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const cart = useCartStore()

const formRef = ref()
const submitting = ref(false)
const directLines = ref([])

const isDirectBuy = computed(() => Boolean(route.query.buy))

const lines = computed(() => {
  if (isDirectBuy.value) return directLines.value
  return cart.checkedItems.map((i) => ({
    product_id: i.product_id,
    name: i.product_name,
    image: i.product_image,
    price: i.price,
    quantity: i.quantity,
    subtotal: i.subtotal,
  }))
})

// 仅用于页面预估展示，真实金额以后端返回为准
const totalAmount = computed(() =>
  lines.value.reduce((sum, l) => sum + Number(l.subtotal), 0).toFixed(2),
)
const freight = computed(() => (Number(totalAmount.value) >= 99 ? '0.00' : '10.00'))
const payAmount = computed(() => (Number(totalAmount.value) + Number(freight.value)).toFixed(2))

const form = reactive({
  receiver_name: '',
  receiver_phone: '',
  receiver_address: '',
  remark: '',
})

const rules = {
  receiver_name: [
    { required: true, message: '请输入收货人姓名', trigger: 'blur' },
    { min: 2, max: 32, message: '长度需在 2-32 位之间', trigger: 'blur' },
  ],
  receiver_phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { min: 6, max: 20, message: '长度需在 6-20 位之间', trigger: 'blur' },
  ],
  receiver_address: [
    { required: true, message: '请输入收货地址', trigger: 'blur' },
    { min: 5, max: 255, message: '长度需在 5-255 位之间', trigger: 'blur' },
  ],
}

async function loadDirectLines() {
  const pairs = String(route.query.buy)
    .split(',')
    .map((chunk) => chunk.split(':'))
    .filter(([id, qty]) => id && Number(qty) > 0)

  const fetched = await Promise.all(
    pairs.map(async ([id, qty]) => {
      const product = await fetchProduct(id).catch(() => null)
      if (!product) return null
      const quantity = Number(qty)
      return {
        product_id: product.id,
        name: product.name,
        image: product.main_image,
        price: product.price,
        quantity,
        subtotal: (Number(product.price) * quantity).toFixed(2),
      }
    }),
  )
  directLines.value = fetched.filter(Boolean)
}

onMounted(async () => {
  if (isDirectBuy.value) {
    await loadDirectLines()
  } else if (!cart.items.length) {
    await cart.refresh()
  }
})

async function onSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  if (!lines.value.length) {
    ElMessage.warning('没有可结算的商品')
    return
  }

  submitting.value = true
  try {
    const payload = { ...form }
    if (!payload.remark) delete payload.remark
    if (isDirectBuy.value) {
      payload.items = lines.value.map((l) => ({ product_id: l.product_id, quantity: l.quantity }))
    }
    const order = await createOrder(payload)
    ElMessage.success(`下单成功，订单号 ${order.order_no}`)
    if (!isDirectBuy.value) await cart.refresh({ silent: true })
    router.replace({ name: 'order-detail', params: { id: order.id } })
  } catch {
    // 库存不足/未勾选商品等提示由拦截器给出
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.page-title {
  margin: 0 0 16px;
  font-size: 20px;
}

.card-title {
  font-weight: 600;
}

.head-tag {
  margin-left: 8px;
}

.line-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.line-thumb {
  width: 46px;
  height: 46px;
  flex: none;
}

.summary-card {
  position: sticky;
  top: 80px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 10px;
  font-size: 14px;
}

.summary-row.total {
  font-size: 15px;
  font-weight: 600;
}

.freight-tip {
  margin: 4px 0 0;
  font-size: 12px;
  color: #909399;
}

.submit-btn {
  width: 100%;
}

.back-btn {
  width: 100%;
  margin-top: 8px;
}
</style>
