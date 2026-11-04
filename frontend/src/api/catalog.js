import http from './http'

// ---------- 分类 ----------
export function fetchCategoryTree(includeHidden = false) {
  return http.get('/categories/tree', { params: { include_hidden: includeHidden } })
}

export function fetchCategories(includeHidden = false) {
  return http.get('/categories', { params: { include_hidden: includeHidden } })
}

export function createCategory(payload) {
  return http.post('/categories', payload)
}

export function updateCategory(id, payload) {
  return http.put(`/categories/${id}`, payload)
}

export function deleteCategory(id) {
  return http.delete(`/categories/${id}`)
}

// ---------- 商品 ----------
export function fetchProducts(params, config = {}) {
  return http.get('/products', { params, ...config })
}

export function fetchProduct(id) {
  return http.get(`/products/${id}`)
}

export function createProduct(payload) {
  return http.post('/products', payload)
}

export function updateProduct(id, payload) {
  return http.put(`/products/${id}`, payload)
}

export function deleteProduct(id) {
  return http.delete(`/products/${id}`)
}

/** 上传裁剪好的商品主图，返回 { url }。 */
export function uploadProductImage(blob) {
  const form = new FormData()
  form.append('file', blob, 'goods.jpg')
  return http.post('/products/image', form)
}
