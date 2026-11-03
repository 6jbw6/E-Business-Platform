import http from './http'

export function createOrder(payload) {
  return http.post('/orders', payload)
}

export function fetchOrders(params) {
  return http.get('/orders', { params })
}

export function fetchOrder(id) {
  return http.get(`/orders/${id}`)
}

export function payOrder(id) {
  return http.put(`/orders/${id}/payment`)
}

export function shipOrder(id) {
  return http.put(`/orders/${id}/shipment`)
}

export function receiveOrder(id) {
  return http.put(`/orders/${id}/receipt`)
}

export function cancelOrder(id) {
  return http.put(`/orders/${id}/cancellation`)
}

/** 后端订单状态的展示口径，集中一处维护 */
export const ORDER_STATUS = [
  { value: 0, label: '待付款', type: 'warning' },
  { value: 1, label: '待发货', type: 'primary' },
  { value: 2, label: '待收货', type: 'success' },
  { value: 3, label: '已完成', type: 'info' },
  { value: 4, label: '已取消', type: 'danger' },
]

export function statusTagType(status) {
  return ORDER_STATUS.find((s) => s.value === status)?.type ?? 'info'
}
