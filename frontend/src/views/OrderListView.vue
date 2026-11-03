<template>
  <div class="page-container">
    <h2 class="page-title">我的订单</h2>

    <el-card shadow="never">
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane v-for="s in ORDER_STATUS" :key="s.value" :label="s.label" :name="String(s.value)" />
      </el-tabs>

      <div v-loading="loading">
        <el-empty v-if="!orders.length && !loading" description="暂无订单">
          <el-button type="primary" @click="router.push({ name: 'home' })">去逛逛</el-button>
        </el-empty>

        <div v-for="order in orders" :key="order.id" class="order-card">
          <div class="order-head">
            <div class="order-head-left">
              <el-tag :type="statusTagType(order.status)" size="small" effect="dark">
                {{ order.status_label }}
              </el-tag>
              <span class="text-muted">订单号 {{ order.order_no }}</span>
              <span class="text-muted">{{ dateTime(order.created_at) }}</span>
            </div>
            <span class="text-muted">
              共 {{ order.item_count }} 种 / {{ order.total_quantity }} 件，实付
              <b class="price">{{ yuan(order.pay_amount) }}</b>
            </span>
          </div>

          <div class="order-body" @click="goDetail(order)">
            <div class="order-summary">
              <span>收货人：{{ order.receiver_name }} {{ order.receiver_phone }}</span>
              <span class="text-muted">地址：{{ order.receiver_address }}</span>
              <span v-if="order.remark" class="text-muted">备注：{{ order.remark }}</span>
            </div>
            <el-icon class="summary-arrow"><ArrowRight /></el-icon>
          </div>

          <div class="order-foot">
            <el-button text @click="goDetail(order)">查看详情</el-button>
            <el-button v-if="order.status === 0" type="danger" size="small" @click="onPay(order)">
              立即付款
            </el-button>
            <el-button v-if="order.status === 0 || order.status === 1" size="small" @click="onCancel(order)">
              取消订单
            </el-button>
            <el-button v-if="order.status === 2" type="success" size="small" @click="onReceive(order)">
              确认收货
            </el-button>
          </div>
        </div>
      </div>

      <el-pagination
        v-if="total > pageSize"
        class="mt-16"
        layout="total, prev, pager, next"
        background
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        @current-change="onPageChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRight } from '@element-plus/icons-vue'

import { ORDER_STATUS, cancelOrder, fetchOrders, payOrder, receiveOrder, statusTagType } from '@/api/orders'
import { dateTime, yuan } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const orders = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(5)
const loading = ref(false)
const activeTab = ref(route.query.status ? String(route.query.status) : 'all')

async function load() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (activeTab.value !== 'all') params.status = Number(activeTab.value)
    const data = await fetchOrders(params)
    orders.value = data.items
    total.value = data.total
  } catch {
    orders.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onTabChange(name) {
  activeTab.value = name
  page.value = 1
  router.replace({ name: 'orders', query: name === 'all' ? {} : { status: name } })
  load()
}

function onPageChange(value) {
  page.value = value
  load()
}

function goDetail(order) {
  router.push({ name: 'order-detail', params: { id: order.id } })
}

async function onPay(order) {
  await ElMessageBox.confirm(`确认支付 ${yuan(order.pay_amount)} 完成本单？（演示为模拟支付）`, '支付确认', {
    type: 'info',
    confirmButtonText: '确认支付',
    cancelButtonText: '再想想',
  }).catch(() => Promise.reject('cancel'))
  await payOrder(order.id)
  ElMessage.success('支付成功，等待商家发货')
  load()
}

async function onCancel(order) {
  await ElMessageBox.confirm('取消后库存会退回商品，已支付的需线下退款，确定取消吗？', '取消订单', {
    type: 'warning',
    confirmButtonText: '确定取消',
    cancelButtonText: '不取消了',
  }).catch(() => Promise.reject('cancel'))
  await cancelOrder(order.id)
  ElMessage.success('订单已取消')
  load()
}

async function onReceive(order) {
  await receiveOrder(order.id)
  ElMessage.success('已确认收货，交易完成')
  load()
}

onMounted(load)
</script>

<style scoped>
.page-title {
  margin: 0 0 16px;
  font-size: 20px;
}

.order-card {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 16px;
  overflow: hidden;
}

.order-head {
  background: #fafafa;
  padding: 10px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  border-bottom: 1px solid #ebeef5;
}

.order-head-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.order-body {
  padding: 12px 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.order-summary {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
}

.summary-arrow {
  color: #c0c4cc;
}

.order-foot {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 14px;
  border-top: 1px dashed #ebeef5;
}
</style>
