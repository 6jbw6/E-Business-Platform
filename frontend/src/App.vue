<template>
  <router-view />
</template>

<script setup>
import { onBeforeUnmount, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useCartStore } from '@/stores/cart'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const user = useUserStore()
const cart = useCartStore()

// 401 由 axios 拦截器派发事件，这里统一收口：清登录态、清购物车、需要登录的页面跳去登录
function handleAuthExpired() {
  user.handleExpired()
  cart.reset()
  if (route.meta.requiresAuth || route.meta.requiresAdmin) {
    router.replace({ name: 'login', query: { redirect: route.fullPath } })
  }
}

onMounted(() => {
  window.addEventListener('mall:auth-expired', handleAuthExpired)
  if (user.isLoggedIn) {
    cart.refresh({ silent: true })
  }
})

onBeforeUnmount(() => window.removeEventListener('mall:auth-expired', handleAuthExpired))

watch(
  () => user.isLoggedIn,
  (loggedIn) => {
    if (loggedIn) {
      cart.refresh({ silent: true })
    } else {
      cart.reset()
    }
  },
)
</script>
