<template>
  <view class="page-layout" :class="{ 'wide-layout': isWide }">
    <!-- H5 大屏布局：顶部工具栏 + 日历主区 + 录入辅助区 -->
    <view v-if="isWide" class="desktop-layout">
      <view class="desktop-nav">
        <text class="desktop-title">学习日历</text>
        <RecordViewer class="record-viewer wide nav-viewer" />
      </view>

      <view class="desktop-content">
        <view class="calendar-section">
          <CalendarPicker
            v-model="selectedDate"
            :record-dates="recordDateSet"
            :partial-dates="partialDateSet"
            :wide="isWide"
            @month-change="onMonthChange"
          />
        </view>

        <view class="entry-section">
          <scroll-view scroll-y class="entry-scroll">
            <InputEntry
              :selected-date="selectedDate"
              :day-record="currentDayRecord"
              @saved="onDataChanged"
              @deleted="onDataChanged"
            />
          </scroll-view>
        </view>
      </view>
    </view>

    <!-- 窄屏（手机）保持原有纵向布局和悬浮按钮 -->
    <view v-if="!isWide" class="mobile-layout">
      <scroll-view scroll-y class="wrapper">
        <CalendarPicker
          v-model="selectedDate"
          :record-dates="recordDateSet"
          :partial-dates="partialDateSet"
          @month-change="onMonthChange"
        />
        <InputEntry
          :selected-date="selectedDate"
          :day-record="currentDayRecord"
          @saved="onDataChanged"
          @deleted="onDataChanged"
        />
      </scroll-view>
      <RecordViewer class="float-viewer" />
    </view>
  </view>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from "vue";
import CalendarPicker from "./CalendarPicker.vue";
import InputEntry from "./InputEntry.vue";
import RecordViewer from "./RecordViewer.vue";
import Global from "@/utils/Global.js";

const selectedDate    = ref(new Date());
const monthRecords    = ref({});
const currentDayRecord = ref(null);
const recordDateSet   = ref(new Set());
const partialDateSet  = ref(new Set());
const isWide          = ref(false);

const formatDate = (date) => {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
};

const isFullRecord = (record) => {
  if (!record) return false;
  const hasReading = !!(record.reading_start && record.reading_end);
  const hasMath = !!(
    record.math_title &&
    (record.math_min || record.math_min === 0) &&
    (record.math_sec || record.math_sec === 0)
  );
  const hasClass = !!(record.class_title && record.class_type);
  return hasReading && hasMath && hasClass;
};

const syncDerivedState = () => {
  const keys = Object.keys(monthRecords.value);
  recordDateSet.value = new Set(keys);

  const partialSet = new Set();
  keys.forEach((key) => {
    const rec = monthRecords.value[key];
    if (rec && !isFullRecord(rec)) {
      partialSet.add(key);
    }
  });
  partialDateSet.value = partialSet;

  const key = formatDate(selectedDate.value);
  currentDayRecord.value = monthRecords.value[key] || null;
};

watch(selectedDate, syncDerivedState);
watch(monthRecords, syncDerivedState, { deep: true });

const fetchMonthRecords = ({ year, month }) => {
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: { method: "getMonthRecords", year, month },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
      if (res.data?.code === 0) {
        const rawData = res.data.data || {};
        const cleanData = {};
        for (const key in rawData) {
          const cleanKey = key.split(" ")[0];
          cleanData[cleanKey] = rawData[key];
        }
        monthRecords.value = cleanData;
      }
    },
    fail: (err) => {
      uni.showToast({ title: "加载记录失败", icon: "none" });
    },
  });
};

const onMonthChange = ({ year, month }) => fetchMonthRecords({ year, month });
const onDataChanged = (dateStr) => {
  const d = new Date(dateStr);
  fetchMonthRecords({ year: d.getFullYear(), month: d.getMonth() + 1 });
};

// 响应式宽度判断
const checkWidth = () => {
  // #ifdef H5
  const width =
    window.innerWidth || document.documentElement?.clientWidth || 0;
  isWide.value = width >= 1024;
  return;
  // #endif

  // 小程序和其他小屏端保持纵向布局，避免 H5 专用大屏样式误入。
  isWide.value = false;
};

onMounted(() => {
  checkWidth();
  // #ifdef H5
  window.addEventListener("resize", checkWidth);
  // #endif

  const now = new Date();
  fetchMonthRecords({ year: now.getFullYear(), month: now.getMonth() + 1 });
});

// #ifdef H5
onUnmounted(() => window.removeEventListener("resize", checkWidth));
// #endif
</script>

<style lang="scss" scoped>
.page-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f7f7f7;

  /* 宽屏左右布局 */
  &.wide-layout {
    padding: 0;
  }
}

.desktop-layout {
  height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  background: #f7f7f7;
  overflow: hidden;
}

.desktop-nav {
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #eeeeee;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  box-sizing: border-box;
  flex-shrink: 0;
}

.desktop-title {
  font-size: 22px;
  font-weight: 700;
  color: #222;
}

.desktop-content {
  min-height: 0;
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 20px 24px 24px;
  box-sizing: border-box;
  overflow: hidden;
}

.calendar-section {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
}

.entry-section {
  flex: 0 0 clamp(320px, 24vw, 430px);
  min-width: 300px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.entry-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.record-viewer.wide {
  position: static;
}

.nav-viewer {
  flex-shrink: 0;
}

:deep(.entry-container) {
  padding: 0;
}

:deep(.entry-container .date-banner) {
  margin-bottom: 16px;
}

:deep(.entry-container .card) {
  margin-bottom: 16px;
  padding: 22px;
}

:deep(.nav-viewer .viewer-btn) {
  margin-bottom: 0;
  padding: 9px 18px;
  border: 1px solid #ffe0e7;
  box-shadow: none;
}

:deep(.nav-viewer .viewer-btn-text) {
  font-size: 15px;
}

/* 窄屏（手机）样式完全保留 */
.mobile-layout {
  height: 100vh;
}
.wrapper {
  height: 100vh;
  background: #f7f7f7;
  padding: 20rpx;
  box-sizing: border-box;
}
.float-viewer {
  position: fixed;
  right: 30rpx;
  bottom: 60rpx;
  z-index: 100;
}

/* #ifdef MP-WEIXIN */
.wrapper {
  padding-bottom: calc(180rpx + constant(safe-area-inset-bottom));
  padding-bottom: calc(180rpx + env(safe-area-inset-bottom));
}

.float-viewer {
  bottom: calc(120rpx + constant(safe-area-inset-bottom));
  bottom: calc(120rpx + env(safe-area-inset-bottom));
}
/* #endif */

/* 宽屏下查看按钮回归正常流 */
.record-viewer.wide {
  position: static;
  margin-top: 0;
}
</style>