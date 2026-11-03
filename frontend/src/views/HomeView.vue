<template>
  <div class="page-container">
    <el-row :gutter="16">
      <el-col :xs="24" :sm="6" :md="5">
        <el-card class="category-card" shadow="never" :body-style="{ padding: '0' }">
          <template #header>
            <span class="card-title">商品分类</span>
          </template>
          <el-menu :default-active="activeCategoryKey" class="category-menu" @select="onSelectCategory">
            <el-menu-item index="all">
              <el-icon><Menu /></el-icon>
              <span>全部商品</span>
            </el-menu-item>
            <el-sub-menu v-for="root in categories" :key="root.id" :index="`root-${root.id}`">
              <!-- 点标题即按一级分类筛选（后端会级联其下所有二级分类），不再额外放一个「（全部）」子项 -->
              <template #title>
                <span class="submenu-title" @click="selectCategory(root.id)">{{ root.name }}</span>
              </template>
              <el-menu-item v-for="child in root.children" :key="child.id" :index="`cat-${child.id}`">
                {{ child.name }}
              </el-menu-item>
            </el-sub-menu>
          </el-menu>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="18" :md="19">
        <el-card class="toolbar-card" shadow="never">
          <div class="toolbar">
            <div class="toolbar-left">
              <el-select v-model="sort" style="width: 160px" @change="onSortChange">
                <el-option label="默认排序" value="default" />
                <el-option label="价格从低到高" value="price_asc" />
                <el-option label="价格从高到低" value="price_desc" />
                <el-option label="销量优先" value="sales_desc" />
                <el-option label="最新上架" value="newest" />
              </el-select>
              <el-input-number
                v-model="minPrice"
                :min="0"
                :controls="false"
                placeholder="最低价"
                style="width: 100px"
              />
              <span class="range-sep">—</span>
              <el-input-number
                v-model="maxPrice"
                :min="0"
                :controls="false"
                placeholder="最高价"
                style="width: 100px"
              />
              <el-button type="primary" plain @click="applyFilters">筛选</el-button>
              <el-button v-if="hasFilters" text @click="resetFilters">清空条件</el-button>
            </div>
            <div class="toolbar-right text-muted">
              共 {{ total }} 件商品
              <template v-if="route.query.keyword">，关键词「{{ route.query.keyword }}」</template>
            </div>
          </div>
        </el-card>

        <div v-loading="loading">
          <el-alert
            v-if="loadError"
            type="error"
            show-icon
            :closable="false"
            :title="`商品加载失败：${loadError}`"
            class="mb-16"
          >
            <el-button size="small" type="primary" @click="load">重试</el-button>
          </el-alert>
          <el-empty v-else-if="!loading && !products.length" description="没有符合条件的商品" />
          <el-row v-if="!loadError" :gutter="12">
            <el-col
              v-for="item in products"
              :key="item.id"
              :xs="12"
              :sm="8"
              :md="6"
              :lg="4"
              class="grid-item"
            >
              <ProductCard :product="item" />
            </el-col>
          </el-row>
        </div>

        <el-pagination
          v-if="total > pageSize"
          class="mt-16"
          layout="prev, pager, next"
          background
          :current-page="page"
          :page-size="pageSize"
          :total="total"
          @current-change="onPageChange"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Menu } from '@element-plus/icons-vue'

import { fetchCategoryTree, fetchProducts } from '@/api/catalog'
import ProductCard from '@/components/ProductCard.vue'

const route = useRoute()
const router = useRouter()

// 首页固定每页 10 条，分页条不再提供条数切换
const DEFAULT_PAGE_SIZE = 10

const categories = ref([])
const products = ref([])
const total = ref(0)
const loading = ref(false)
const loadError = ref('')

const sort = ref(route.query.sort || 'default')
const minPrice = ref(route.query.min_price ? Number(route.query.min_price) : undefined)
const maxPrice = ref(route.query.max_price ? Number(route.query.max_price) : undefined)
const page = ref(Number(route.query.page) || 1)
const pageSize = ref(DEFAULT_PAGE_SIZE)

const activeCategoryKey = computed(() => {
  const id = route.query.category_id
  return id ? `cat-${id}` : 'all'
})

const hasFilters = computed(
  () => Boolean(route.query.keyword || route.query.category_id || route.query.min_price || route.query.max_price),
)

function buildQuery(overrides = {}) {
  const query = {
    keyword: route.query.keyword,
    category_id: route.query.category_id,
    min_price: route.query.min_price,
    max_price: route.query.max_price,
    sort: sort.value,
    page: page.value,
    ...overrides,
  }
  Object.keys(query).forEach((key) => {
    if (query[key] === undefined || query[key] === '' || query[key] === null) delete query[key]
  })
  return query
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const data = await fetchProducts({
      keyword: route.query.keyword,
      category_id: route.query.category_id,
      min_price: route.query.min_price,
      max_price: route.query.max_price,
      sort: route.query.sort || 'default',
      page: Number(route.query.page) || 1,
      page_size: DEFAULT_PAGE_SIZE,
    })
    products.value = data.items
    total.value = data.total
  } catch (error) {
    products.value = []
    total.value = 0
    loadError.value = error?.message || '后端服务不可用'
  } finally {
    loading.value = false
  }
}

function onSelectCategory(index) {
  const query = buildQuery({ page: 1 })
  if (index === 'all') {
    delete query.category_id
  } else if (index.startsWith('cat-')) {
    query.category_id = index.slice(4)
  }
  router.push({ name: 'home', query })
}

// 点一级分类标题：直接按该一级分类筛选，后端会级联它下面所有二级分类的商品
function selectCategory(rootId) {
  router.push({ name: 'home', query: buildQuery({ page: 1, category_id: rootId }) })
}

function applyFilters() {
  page.value = 1
  router.push({
    name: 'home',
    query: buildQuery({
      page: 1,
      min_price: minPrice.value,
      max_price: maxPrice.value,
    }),
  })
}

function resetFilters() {
  minPrice.value = undefined
  maxPrice.value = undefined
  sort.value = 'default'
  router.push({ name: 'home', query: { page: 1 } })
}

function onSortChange() {
  page.value = 1
  router.push({ name: 'home', query: buildQuery({ page: 1 }) })
}

function onPageChange(value) {
  page.value = value
  router.push({ name: 'home', query: buildQuery({ page: value }) })
}

// 顶栏搜索框改的是 URL，这里跟着重新拉数据
watch(
  () => route.query,
  () => {
    if (route.name !== 'home') return
    sort.value = route.query.sort || 'default'
    minPrice.value = route.query.min_price ? Number(route.query.min_price) : undefined
    maxPrice.value = route.query.max_price ? Number(route.query.max_price) : undefined
    page.value = Number(route.query.page) || 1
    load()
  },
)

onMounted(async () => {
  try {
    categories.value = await fetchCategoryTree()
  } catch {
    categories.value = []
  }
  load()
})
</script>

<style scoped>
.category-card {
  margin-bottom: 16px;
}

.card-title {
  font-weight: 600;
}

.category-menu {
  border-right: none;
}

.submenu-title {
  /* 一级分类标题本身可点，点下去就是「这一大类的全部商品」 */
  pointer-events: auto;
  flex: 1;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.range-sep {
  color: #c0c4cc;
}

.grid-item {
  margin-bottom: 12px;
}
</style>
