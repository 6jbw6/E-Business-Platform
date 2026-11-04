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
          <el-option v-for="c in mainCategories" :key="c.id" :label="c.name" :value="c.id" />
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
            <el-option-group v-for="group in categoryGroups" :key="group.id" :label="group.name">
              <el-option :value="group.id" :label="group.name" />
              <el-option v-for="child in group.children" :key="child.id" :value="child.id" :label="child.name" />
            </el-option-group>
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
        <el-form-item label="商品主图">
          <div class="image-pick" title="点击上传主图" @click="pickImage">
            <el-image v-if="form.main_image" :src="form.main_image" fit="cover" class="image-preview">
              <template #error>
                <div class="image-placeholder">
                  <span>图片读不出</span>
                  <span>点击重新上传</span>
                </div>
              </template>
            </el-image>
            <div v-else class="image-placeholder">
              <el-icon :size="22"><Plus /></el-icon>
              <span>点击上传</span>
            </div>
          </div>
          <input
            ref="fileInputRef"
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp"
            class="hidden-input"
            @change="onFilePicked"
          />
        </el-form-item>
        <el-form-item label="图文详情">
          <el-input v-model="form.detail" type="textarea" :rows="3" maxlength="2000" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="cropVisible" title="裁剪商品主图" width="560px" @closed="releaseObjectUrl">
      <div class="crop-wrap">
        <Cropper
          :src="cropSource"
          :stencil-props="{ aspectRatio: IMAGE_ASPECT_RATIO }"
          class="cropper-box"
          @change="onCropChange"
        />
        <span class="text-muted crop-hint">拖动图片、缩放矩形选区，框内的部分就是最终主图</span>
      </div>
      <template #footer>
        <el-button @click="cropVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" :disabled="!cropCanvas" @click="onConfirmCrop">
          上传主图
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { Cropper } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'

import {
  createProduct,
  fetchCategories,
  fetchProduct,
  fetchProducts,
  updateProduct,
  uploadProductImage,
} from '@/api/catalog'
import { yuan } from '@/utils/format'

const MAX_PICK_BYTES = 5 * 1024 * 1024
const IMAGE_OUTPUT_WIDTH = 800
const IMAGE_ASPECT_RATIO = 4 / 3

const items = ref([])
const categories = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)

const filters = reactive({ keyword: '', category_id: undefined, show_all: true })

// 筛选只列一级分类：后端传一级 ID 会级联它下面所有二级分类的商品
const mainCategories = computed(() => categories.value.filter((c) => c.level === 1))

// 发布/编辑仍要能选到二级，否则会把已有商品的分类从二级挪到一级
const categoryGroups = computed(() =>
  mainCategories.value.map((root) => ({
    ...root,
    children: categories.value.filter((c) => c.parent_id === root.id),
  })),
)

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

const fileInputRef = ref()
const cropVisible = ref(false)
const cropSource = ref('')
const cropCanvas = ref(null)
const uploading = ref(false)

function pickImage() {
  fileInputRef.value?.click()
}

function releaseObjectUrl() {
  if (cropSource.value) URL.revokeObjectURL(cropSource.value)
  cropSource.value = ''
  cropCanvas.value = null
}

function onFilePicked(event) {
  const input = event.target
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (file.size > MAX_PICK_BYTES) {
    ElMessage.warning(`图片太大（${(file.size / 1024 / 1024).toFixed(1)} MB），请选 5 MB 以内的`)
    return
  }
  releaseObjectUrl()
  cropSource.value = URL.createObjectURL(file)
  cropVisible.value = true
}

// 裁剪库在选区变化时给出已裁好的 canvas，直接拿它做导出源
function onCropChange({ canvas }) {
  cropCanvas.value = canvas ?? null
}

function toRectJpeg(source) {
  return new Promise((resolve) => {
    const width = IMAGE_OUTPUT_WIDTH
    const height = Math.round(width / IMAGE_ASPECT_RATIO)
    const output = document.createElement('canvas')
    output.width = width
    output.height = height
    const ctx = output.getContext('2d')
    // JPEG 没有透明通道，先铺白底，否则带透明的 PNG 传上去会变黑底
    ctx.fillStyle = '#fff'
    ctx.fillRect(0, 0, width, height)
    ctx.drawImage(source, 0, 0, width, height)
    output.toBlob((blob) => resolve(blob), 'image/jpeg', 0.92)
  })
}

async function onConfirmCrop() {
  if (!cropCanvas.value) {
    ElMessage.warning('还没有可上传的裁剪结果')
    return
  }
  const blob = await toRectJpeg(cropCanvas.value)
  if (!blob) {
    ElMessage.error('图片导出失败，请换一张试试')
    return
  }
  uploading.value = true
  try {
    const data = await uploadProductImage(blob)
    form.main_image = data.url
    ElMessage.success('主图已上传，点「确定」保存商品后生效')
    cropVisible.value = false
  } catch {
    // 类型不合法、图片过大等提示由拦截器给出
  } finally {
    uploading.value = false
  }
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

/* 主图选框按 4:3 长方形展示，和裁剪弹窗里的比例一致 */
.image-pick {
  width: 160px;
  height: 120px;
  border: 1px dashed #c0c4cc;
  border-radius: 6px;
  cursor: pointer;
  overflow: hidden;
}

.image-pick:hover {
  border-color: var(--brand-color);
}

.image-preview {
  width: 100%;
  height: 100%;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: #909399;
  font-size: 13px;
  background: #f7f8fa;
}

.hidden-input {
  display: none;
}

.crop-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cropper-box {
  height: 340px;
  background: #f0f2f5;
}

.crop-hint {
  text-align: center;
}
</style>
