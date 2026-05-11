<template>
  <view class="app-container">
    <MyCalendar />
  </view>
</template>

<script setup>
import MyCalendar from '@/components/MyCalendar/MyCalendar.vue';
</script>

<style lang="scss">
.app-container {
  background-color: #f7f8fa;
  min-height: 100vh;
  padding-bottom: 50rpx;
}
</style>