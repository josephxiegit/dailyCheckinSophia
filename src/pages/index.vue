<template>
  <view class="app-container">
    <MyCalendar />
  </view>
</template>

<script setup>
import MyCalendar from '@/components/MyCalendar/MyCalendar.vue';
</script>

<style lang="scss">
page {
  height: 100%;
  overflow: hidden;
}

.app-container {
  background-color: #f7f8fa;
  height: 100vh;
  height: 100svh;
  height: 100dvh;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
</style>
