<template>
  <div class="not-found">
    <el-result icon="warning" title="404" sub-title="这个页面不存在，可能是地址输错了">
      <template #extra>
        <el-button type="primary" @click="router.push({ name: 'home' })">返回商城首页</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
