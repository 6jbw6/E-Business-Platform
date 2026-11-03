<template>
  <div>
    <el-card shadow="never" class="mb-16">
      <div class="toolbar">
        <el-radio-group v-model="statusFilter" @change="reload(1)">
          <el-radio-button :value="1">待发货</el-radio-button>
          <el-radio-button :value="0">待付款</el-radio-button>
          <el-radio-button :value="2">待收货</el-radio-button>
          <el-radio-button :value="3">已完成</el-radio-button>
          <el-radio-button :value="4">已取消</el-radio-button>
          <el-radio-button :value="null">全部</el-radio-button>
        </el-radio-group>
        <el-button :icon="Refresh" @click="reload()">刷新</el-button>
        <span class="text-muted">共 {{ total }} 笔订单；发货后买家才能确认收货</span>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="orders" style="width: 100%" @expand-change="onExpand">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-box" v-loading="!row._items">
              <el-table v-if="row._items" :data="row._items" size="small">
                <el-table-column label="商品" min-width="220" prop="product_name" />
                <el-table-column label="成交单价" width="120" align="right">
                  <template #default="scope">{{ yuan(scope.row.price) }}</template>
                </el-table-column>
                <el-table-column label="数量" width="90" align="center" prop="quantity" />
                <el-table-column label="小计" width="120" align="right">
                  <template #default="scope">{{ yuan(scope.row.subtotal) }}</template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="订单号" min-width="190">
          <template #default="{ row }">
            <span class="mono">{{ row.order_no }}</span>
          </template>
        </el-table-column>
        <el-table-column label="收货人" width="170">
          <template #default="{ row }">
            <div class="name-cell">
              <span>{{ row.receiver_name }}</span>
              <span class="text-muted">{{ row.receiver_phone }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="收货地址" min-width="220" show-overflow-tooltip prop="receiver_address" />
        <el-table-column label="金额" width="120" align="right">
          <template #default="{ row }"><span class="price">{{ yuan(row.pay_amount) }}</span></template>
        </el-table-column>
        <el-table-column label="件数" width="100" align="center">
          <template #default="{ row }">{{ row.item_count }} 种 / {{ row.total_quantity }} 件</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)" effect="dark">{{ row.status_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="下单时间" width="160">
          <template #default="{ row }">{{ dateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 1"
              type="primary"
              size="small"
              :loading="shippingId === row.id"
              @click="onShip(row)"
            >
              发货
            </el-button>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="mt-16"
        layout="total, sizes, prev, pager, next, jumper"
        background
        :current-page="page"
        :page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="total"
        @current-change="reload"
        @size-change="onSizeChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

import { fetchOrder, fetchOrders, shipOrder, statusTagType } from '@/api/orders'
import { dateTime, yuan } from '@/utils/format'

const orders = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const statusFilter = ref(1)
const shippingId = ref(null)

async function reload(targetPage = page.value) {
  loading.value = true
  page.value = targetPage
  try {
    const params = { all: true, page: targetPage, page_size: pageSize.value }
    if (statusFilter.value !== null) params.status = statusFilter.value
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

function onSizeChange(value) {
  pageSize.value = value
  reload(1)
}

async function onShip(row) {
  await ElMessageBox.confirm(`确定把订单 ${row.order_no} 标记为已发货吗？`, '发货确认', {
    type: 'info',
    confirmButtonText: '发货',
    cancelButtonText: '取消',
  }).catch(() => Promise.reject('cancel'))

  shippingId.value = row.id
  try {
    await shipOrder(row.id)
    ElMessage.success('已发货，等待买家确认收货')
    // 重新拉列表，否则本行会带着「待收货」状态留在「待发货」筛选结果里
    await reload()
  } catch {
    // 状态机不允许等提示由拦截器给出
  } finally {
    shippingId.value = null
  }
}

// 展开行时才拉明细，避免列表页 N+1 请求
async function onExpand(row, expandedRows) {
  if (!expandedRows.includes(row) || row._items) return
  const detail = await fetchOrder(row.id).catch(() => null)
  row._items = detail?.items ?? []
}

onMounted(() => reload(1))
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.expand-box {
  padding: 8px 40px;
  min-height: 48px;
}

.mono {
  font-family: Consolas, Monaco, monospace;
  font-size: 13px;
}

.name-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>
