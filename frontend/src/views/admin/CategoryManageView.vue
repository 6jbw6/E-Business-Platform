<template>
  <div>
    <el-card shadow="never" class="mb-16">
      <div class="toolbar">
        <el-button type="primary" :icon="Plus" @click="openCreate(null)">新建一级分类</el-button>
        <el-switch v-model="includeHidden" active-text="显示隐藏分类" @change="load" />
        <span class="text-muted">最多支持两级分类；分类下有商品时不能删除</span>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="tree"
        row-key="id"
        default-expand-all
        :tree-props="{ children: 'children' }"
      >
        <el-table-column label="分类名称" min-width="220" prop="name" />
        <el-table-column label="ID" width="80" prop="id" />
        <el-table-column label="层级" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.level === 1 ? 'primary' : 'info'" effect="plain">
              {{ row.level === 1 ? '一级' : '二级' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="排序" width="90" prop="sort_order" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 1 ? 'success' : 'warning'" effect="plain">
              {{ row.status === 1 ? '显示' : '隐藏' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <div class="op-cell">
              <el-button v-if="row.level === 1" text type="primary" size="small" @click="openCreate(row)">
                加子分类
              </el-button>
              <!-- 二级分类没有「加子分类」，但占位仍要留，否则后面两个按钮会整体左移 -->
              <el-button v-else text size="small" class="op-placeholder" tabindex="-1" aria-hidden="true">
                加子分类
              </el-button>
              <el-button text size="small" @click="openEdit(row)">编辑</el-button>
              <el-button text type="danger" size="small" @click="onDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="上级分类">
          <el-input :model-value="parentName" disabled placeholder="顶级（一级分类）" />
        </el-form-item>
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="form.name" maxlength="50" placeholder="1-50 位" />
        </el-form-item>
        <el-form-item label="图标地址">
          <el-input v-model="form.icon" maxlength="255" placeholder="选填" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">显示</el-radio>
            <el-radio :value="0">隐藏</el-radio>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

import { createCategory, deleteCategory, fetchCategoryTree, updateCategory } from '@/api/catalog'

const tree = ref([])
const loading = ref(false)
const includeHidden = ref(true)

const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref()
const editingId = ref(null)
const parentName = ref('')

const form = reactive({ name: '', icon: '', sort_order: 0, status: 1, parent_id: null })

const rules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { max: 50, message: '名称不超过 50 位', trigger: 'blur' },
  ],
}

const dialogTitle = computed(() =>
  editingId.value ? '编辑分类' : form.parent_id ? '新建二级分类' : '新建一级分类',
)

async function load() {
  loading.value = true
  try {
    tree.value = await fetchCategoryTree(includeHidden.value)
  } catch {
    tree.value = []
  } finally {
    loading.value = false
  }
}

function resetForm(parent = null, row = null) {
  editingId.value = row?.id ?? null
  parentName.value = row ? (row.parent_id ? findName(row.parent_id) : '顶级（一级分类）') : parent ? parent.name : ''
  form.name = row?.name ?? ''
  form.icon = row?.icon ?? ''
  form.sort_order = row?.sort_order ?? 0
  form.status = row?.status ?? 1
  form.parent_id = row ? row.parent_id : parent?.id ?? null
}

function findName(id) {
  for (const root of tree.value) {
    if (root.id === id) return root.name
    const child = (root.children ?? []).find((c) => c.id === id)
    if (child) return child.name
  }
  return `ID ${id}`
}

function openCreate(parent) {
  resetForm(parent)
  dialogVisible.value = true
}

function openEdit(row) {
  resetForm(null, row)
  dialogVisible.value = true
}

async function onSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editingId.value) {
      const { name, icon, sort_order, status } = form
      await updateCategory(editingId.value, { name, icon, sort_order, status })
      ElMessage.success('分类已更新')
    } else {
      const payload = { name: form.name, icon: form.icon, sort_order: form.sort_order, status: form.status }
      if (form.parent_id) payload.parent_id = form.parent_id
      await createCategory(payload)
      ElMessage.success('分类已创建')
    }
    dialogVisible.value = false
    load()
  } catch {
    // 同级重名、层级超限等提示由拦截器给出
  } finally {
    saving.value = false
  }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确定删除分类「${row.name}」吗？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  }).catch(() => Promise.reject('cancel'))
  await deleteCategory(row.id)
  ElMessage.success('分类已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}

/* 三个按钮各占固定宽度，一级/二级行的「编辑」「删除」才能竖向对齐 */
.op-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.op-cell :deep(.el-button) {
  margin-left: 0;
  min-width: 62px;
}

.op-placeholder {
  visibility: hidden;
  pointer-events: none;
}
</style>
