import { defineStore } from 'pinia'
import { addToCart, clearCart, fetchCart, removeCartItem, updateCartItem } from '@/api/cart'

export const useCartStore = defineStore('cart', {
  state: () => ({
    items: [],
    totalQuantity: 0,
    totalAmount: '0.00',
    checkedCount: 0,
    loading: false,
  }),
  getters: {
    /** 顶部购物车角标显示勾选件数 */
    badge: (state) => (state.totalQuantity > 99 ? '99+' : state.totalQuantity),
    checkedItems: (state) => state.items.filter((i) => i.checked === 1),
  },
  actions: {
    async refresh({ silent = true } = {}) {
      this.loading = true
      try {
        const data = await fetchCart({ silent })
        this.apply(data)
        return data
      } finally {
        this.loading = false
      }
    },
    apply(data) {
      if (!data) {
        this.items = []
        this.totalQuantity = 0
        this.totalAmount = '0.00'
        this.checkedCount = 0
        return
      }
      this.items = data.items ?? []
      this.totalQuantity = data.total_quantity ?? 0
      this.totalAmount = data.total_amount ?? '0.00'
      this.checkedCount = data.checked_count ?? 0
    },
    async add(productId, quantity = 1) {
      const data = await addToCart(productId, quantity)
      this.apply(data)
      return data
    },
    async updateItem(itemId, payload) {
      const data = await updateCartItem(itemId, payload)
      this.apply(data)
      return data
    },
    async removeItem(itemId) {
      const data = await removeCartItem(itemId)
      this.apply(data)
      return data
    },
    async clear() {
      const data = await clearCart()
      this.apply(data)
      return data
    },
    reset() {
      this.apply(null)
    },
  },
})
