import http from './http'

export function fetchCart(config = {}) {
  return http.get('/cart', config)
}

export function addToCart(productId, quantity = 1) {
  return http.post('/cart', { product_id: productId, quantity })
}

export function updateCartItem(itemId, payload) {
  return http.put(`/cart/${itemId}`, payload)
}

export function removeCartItem(itemId) {
  return http.delete(`/cart/${itemId}`)
}

export function clearCart() {
  return http.delete('/cart')
}
