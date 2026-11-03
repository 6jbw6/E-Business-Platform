<template>
  <div class="page-container" v-loading="loading">
    <div class="head-row">
      <h2 class="page-title">订单详情</h2>
      <el-button text @click="router.push({ name: 'orders' })">
        <el-icon><ArrowLeft /></el-icon>
        返回我的订单
      </el-button>
    </div>

    <template v-if="order">
      <el-card shadow="never" class="mb-16">
        <el-steps :active="stepActive" align-center finish-status="success" :process-status="order.status === 4 ? 'error' : 'process'">
          <el-step title="提交订单" :description="dateTime(order.created_at)" />
          <el-step title="付款" :description="dateTime(order.paid_at)" />
          <el-step title="发货" :description="dateTime(order.shipped_at)" />
          <el-step title="交易完成" :description="dateTime(order.finished_at)" />
        </el-steps>
        <el-alert
          v-if="order.status === 4"
          class="mt-16"
          type="warning"
          show-icon
          :closable="false"
          :title="`该订单已于 ${dateTime(order.cancelled_at)} 取消，库存已退回商品`"
        />
      </el-card>

      <el-row :gutter="16">
        <el-col :xs="24" :md="16">
          <el-card shadow="never" class="mb-16">
            <template #header><span class="card-title">商品清单</span></template>
            <el-table :data="order.items">
              <el-table-column label="商品" min-width="240">
                <template #default="{ row }">
                  <div class="line-name">
                    <el-image :src="row.product_image" fit="cover" class="line-thumb">
                      <template #error>
                        <div class="thumb-fallback line-thumb">
                          <span>{{ row.product_name.slice(0, 2) }}</span>
                        </div>
                      </template>
                    </el-image>
                    <router-link
                      :to="{ name: 'product-detail', params: { id: row.product_id } }"
                      class="link"
                    >
                      {{ row.product_name }}
                    </router-link>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="成交单价" width="120" align="right">
                <template #default="{ row }">{{ yuan(row.price) }}</template>
              </el-table-column>
              <el-table-column label="数量" width="80" align="center">
                <template #default="{ row }">{{ row.quantity }}</template>
              </el-table-column>
              <el-table-column label="小计" width="120" align="right">
                <template #default="{ row }">
                  <span class="price">{{ yuan(row.subtotal) }}</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <el-card shadow="never">
            <template #header><span class="card-title">收货信息</span></template>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="收货人">{{ order.receiver_name }}</el-descriptions-item>
              <el-descriptions-item label="联系电话">{{ order.receiver_phone }}</el-descriptions-item>
              <el-descriptions-item label="收货地址">{{ order.receiver_address }}</el-descriptions-item>
              <el-descriptions-item label="买家备注">{{ order.remark || '无' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="summary-card">
            <template #header><span class="card-title">订单信息</span></template>
            <div class="summary-row">
              <span>订单号</span>
              <span class="mono">{{ order.order_no }}</span>
            </div>
            <div class="summary-row">
              <span>当前状态</span>
              <el-tag :type="statusTagType(order.status)" size="small" effect="dark">
                {{ order.status_label }}
              </el-tag>
            </div>
            <div class="summary-row">
              <span>商品总额</span>
              <span>{{ yuan(order.total_amount) }}</span>
            </div>
            <div class="summary-row">
              <span>运费</span>
              <span>{{ yuan(order.freight) }}</span>
            </div>
            <el-divider />
            <div class="summary-row total">
              <span>实付金额</span>
              <span class="price price-large">{{ yuan(order.pay_amount) }}</span>
            </div>
            <div class="action-col">
              <el-button v-if="order.status === 0" type="danger" @click="onPay">立即付款</el-button>
              <el-button v-if="order.status === 2" type="success" @click="onReceive">确认收货</el-button>
              <el-button
                v-if="order.status === 0 || order.status === 1"
                @click="onCancel"
              >
                取消订单
              </el-button>
              <el-tag v-if="order.status === 1" type="info" effect="plain">已付款，等待商家发货</el-tag>
              <el-tag v-if="order.status === 3" type="success" effect="plain">交易已完成</el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <el-empty v-else-if="!loading" description="订单不存在或无权查看" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'

import { cancelOrder, fetchOrder, payOrder, receiveOrder, statusTagType } from '@/api/orders'
import { dateTime, yuan } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const order = ref(null)
const loading = ref(false)

// 已取消(4) 时不再推进步骤条
const stepActive = computed(() => {
  const status = order.value?.status
  if (status === undefined || status === 4) return 0
  return status + 1
})

async function load() {
  loading.value = true
  try {
    order.value = await fetchOrder(route.params.id)
  } catch {
    order.value = null
  } finally {
    loading.value = false
  }
}

async function onPay() {
  await ElMessageBox.confirm(`确认支付 ${yuan(order.value.pay_amount)} 完成本单？（演示为模拟支付）`, '支付确认', {
    type: 'info',
    confirmButtonText: '确认支付',
    cancelButtonText: '再想想',
  }).catch(() => Promise.reject('cancel'))
  order.value = await payOrder(order.value.id)
  ElMessage.success('支付成功，等待商家发货')
}

async function onReceive() {
  order.value = await receiveOrder(order.value.id)
  ElMessage.success('已确认收货，交易完成')
}

async function onCancel() {
  await ElMessageBox.confirm('取消后库存会退回商品，已支付的需线下退款，确定取消吗？', '取消订单', {
    type: 'warning',
    confirmButtonText: '确定取消',
    cancelButtonText: '不取消了',
  }).catch(() => Promise.reject('cancel'))
  order.value = await cancelOrder(order.value.id)
  ElMessage.success('订单已取消')
}

onMounted(load)
</script>

<style scoped>
.head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.page-title {
  margin: 0;
  font-size: 20px;
}

.card-title {
  font-weight: 600;
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

.link {
  color: #303133;
  text-decoration: none;
}

.link:hover {
  color: var(--brand-color);
}

.summary-card {
  position: sticky;
  top: 80px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 14px;
  gap: 12px;
}

.summary-row.total {
  font-weight: 600;
}

.mono {
  font-family: Consolas, Monaco, monospace;
  font-size: 13px;
  word-break: break-all;
}

.action-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
}
</style>
