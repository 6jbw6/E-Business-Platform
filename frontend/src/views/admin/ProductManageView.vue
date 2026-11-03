<template>
  <div>
    <el-card shadow="never" class="mb-16">
      <div class="toolbar">
        <el-input
          v-model="filters.keyword"
          placeholder="按商品名/卖点搜索"
          clearable
          style="width: 220px"
          @keyup.enter="reload(1)"
          @clear="reload(1)"
        />
        <el-select v-model="filters.category_id" placeholder="全部分类" clearable style="width: 180px">
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-switch v-model="filters.show_all" active-text="含已下架" />
        <el-button type="primary" @click="reload(1)">查询</el-button>
        <el-button :icon="Plus" @click="openCreate">发布商品</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="items" style="width: 100%">
        <el-table-column label="主图" width="80">
          <template #default="{ row }">
            <el-image :src="row.main_image" fit="cover" class="thumb">
              <template #error>
                <div class="thumb-fallback thumb"><span>{{ row.name.slice(0, 2) }}</span></div>
              </template>
            </el-image>
          </template>
        </el-table-column>
        <el-table-column label="商品名称" min-width="220">
          <template #default="{ row }">
            <div class="name-cell">
              <span class="strong">{{ row.name }}</span>
              <span class="text-muted">{{ row.subtitle }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="分类" width="130">
          <template #default="{ row }">{{ row.category_name || `#${row.category_id}` }}</template>
        </el-table-column>
        <el-table-column label="售价" width="110" align="right">
          <template #default="{ row }"><span class="price">{{ yuan(row.price) }}</span></template>
        </el-table-column>
        <el-table-column label="库存" width="90" align="right">
          <template #default="{ row }">
            <span :class="{ 'text-danger': row.stock <= 0 }">{{ row.stock }}</span>
          </template>
        </el-table-column>
        <el-table-column label="销量" width="90" align="right" prop="sales" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 1 ? 'success' : 'info'" effect="plain">
              {{ row.status === 1 ? '在售' : '已下架' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button
              v-if="row.status === 1"
              text
              type="danger"
              size="small"
              @click="onToggleStatus(row, 0)"
            >
              下架
            </el-button>
            <el-button v-else text type="success" size="small" @click="onToggleStatus(row, 1)">
              重新上架
            </el-button>
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑商品' : '发布商品'" width="620px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
        <el-form-item label="所属分类" prop="category_id">
          <el-select v-model="form.category_id" placeholder="请选择分类" style="width: 100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="商品名称" prop="name">
          <el-input v-model="form.name" maxlength="120" show-word-limit />
        </el-form-item>
        <el-form-item label="副标题">
          <el-input v-model="form.subtitle" maxlength="200" show-word-limit />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="售价(元)" prop="price">
              <el-input-number v-model="form.price" :min="0.01" :precision="2" :step="10" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="划线价(元)">
              <el-input-number v-model="form.original_price" :min="0" :precision="2" :step="10" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="库存" prop="stock">
              <el-input-number v-model="form.stock" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计量单位">
              <el-input v-model="form.unit" maxlength="16" placeholder="件 / 台 / 只" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="主图地址">
          <el-input v-model="form.main_image" maxlength="255" placeholder="例如 /static/goods/0001.jpg" />
        </el-form-item>
        <el-form-item label="图文详情">
          <el-input v-model="form.detail" type="textarea" :rows="3" maxlength="2000" show-word-limit />
        </el-form-item>
        <el-form-item label="上架状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">在售</el-radio>
            <el-radio :value="0">下架</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

import { createProduct, fetchCategories, fetchProduct, fetchProducts, updateProduct } from '@/api/catalog'
import { yuan } from '@/utils/format'

const items = ref([])
const categories = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)

const filters = reactive({ keyword: '', category_id: undefined, show_all: true })

const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref(null)
const formRef = ref()

const form = reactive({
  category_id: undefined,
  name: '',
  subtitle: '',
  main_image: '',
  price: 99,
  original_price: 0,
  stock: 0,
  unit: '件',
  detail: '',
  status: 1,
})

const rules = {
  category_id: [{ required: true, message: '请选择所属分类', trigger: 'change' }],
  name: [
    { required: true, message: '请输入商品名称', trigger: 'blur' },
    { max: 120, message: '名称不超过 120 位', trigger: 'blur' },
  ],
  price: [{ required: true, message: '请输入售价', trigger: 'blur' }],
}

async function reload(targetPage = page.value) {
  loading.value = true
  page.value = targetPage
  try {
    const data = await fetchProducts({
      keyword: filters.keyword || undefined,
      category_id: filters.category_id || undefined,
      show_all: filters.show_all,
      page: targetPage,
      page_size: pageSize.value,
    })
    items.value = data.items
    total.value = data.total
  } catch {
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onSizeChange(value) {
  pageSize.value = value
  reload(1)
}

function resetForm(row = null) {
  editingId.value = row?.id ?? null
  form.category_id = row?.category_id ?? filters.category_id ?? undefined
  form.name = row?.name ?? ''
  form.subtitle = row?.subtitle ?? ''
  form.main_image = row?.main_image ?? ''
  form.price = row ? Number(row.price) : 99
  form.original_price = row ? Number(row.original_price) : 0
  form.stock = row?.stock ?? 0
  form.unit = row?.unit ?? '件'
  form.detail = row?.detail ?? ''
  form.status = row?.status ?? 1
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

async function openEdit(row) {
  // 列表接口不返回图文详情，编辑前先取一次详情，避免保存时把详情清空
  const detail = await fetchProduct(row.id).catch(() => ({}))
  resetForm({ ...row, ...detail })
  dialogVisible.value = true
}

async function onSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload = { ...form }
    if (editingId.value) {
      await updateProduct(editingId.value, payload)
      ElMessage.success('商品已更新')
    } else {
      await createProduct(payload)
      ElMessage.success('商品已上架')
    }
    dialogVisible.value = false
    reload()
  } catch {
    // 重名、分类不存在等提示由拦截器给出
  } finally {
    saving.value = false
  }
}

async function onToggleStatus(row, nextStatus) {
  const label = nextStatus === 1 ? '重新上架' : '下架'
  await ElMessageBox.confirm(`确定${label}「${row.name}」吗？`, `${label}确认`, {
    type: 'warning',
    confirmButtonText: label,
    cancelButtonText: '取消',
  }).catch(() => Promise.reject('cancel'))
  await updateProduct(row.id, { status: nextStatus })
  ElMessage.success(`已${label}`)
  reload()
}

onMounted(async () => {
  try {
    categories.value = await fetchCategories(true)
  } catch {
    categories.value = []
  }
  reload(1)
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.thumb {
  width: 46px;
  height: 46px;
}

.name-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.strong {
  font-weight: 600;
}

.text-danger {
  color: var(--brand-color);
  font-weight: 600;
}
</style>
