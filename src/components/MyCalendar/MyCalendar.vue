<template>
  <view class="page-layout" :class="{ 'wide-layout': isWide }">
    <view v-if="isWide" class="desktop-layout">
      <view class="desktop-nav">
        <text class="desktop-title">学习日历</text>
        </view>

      <view class="desktop-content">
        <view class="calendar-section">
          <CalendarPicker
            v-model="selectedDate"
            :record-dates="recordDateSet"
            :partial-dates="partialDateSet"
            :wide="isWide"
            @month-change="onMonthChange"
            @open-range-viewer="handleOpenViewer"
          />
        </view>

        <view class="entry-section">
          <view class="entry-scroll">
            <InputEntry
              :selected-date="selectedDate"
              :day-record="currentDayRecord"
              @saved="onDataChanged"
              @deleted="onDataChanged"
            />
          </view>
        </view>
      </view>
    </view>

    <view v-if="!isWide" class="mobile-layout">
      <scroll-view scroll-y class="wrapper">
        <CalendarPicker
          v-model="selectedDate"
          :record-dates="recordDateSet"
          :partial-dates="partialDateSet"
          @month-change="onMonthChange"
          @open-range-viewer="handleOpenViewer" 
        />
        <InputEntry
          :selected-date="selectedDate"
          :day-record="currentDayRecord"
          @saved="onDataChanged"
          @deleted="onDataChanged"
        />
      </scroll-view>
    </view>

    <RecordViewer ref="recordViewerRef" />
    
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
const recordViewerRef = ref(null);

// 触发弹窗
const handleOpenViewer = () => {
  if (recordViewerRef.value) {
    // 调用 RecordViewer.vue 里面的 openPicker 方法
    recordViewerRef.value.openPicker();
  }
};

// === 新增：存储免除名单 ===
const exclusionsList = ref([]);

const formatDate = (date) => {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
};

// === 新增：加载后端的免除名单 ===
const loadExclusions = () => {
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: { method: "getExclusions" },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
      if (res.data?.code === 0) {
        exclusionsList.value = res.data.exclusions || [];
        syncDerivedState(); // 名单拉取后，重新计算圆点
      }
    },
  });
};

// 辅助函数：判断某天某项是否被免除
const isExcluded = (dateStr, section) => {
  return exclusionsList.value.includes(`${dateStr}:${section}`);
};

// === 核心逻辑升级：合并计算录入记录与免除名单 ===
const syncDerivedState = () => {
  const fullSet = new Set();
  const partialSet = new Set();

  // 把“有记录的日期”和“有免除项的日期”全部收集起来遍历
  const datesToCheck = new Set(Object.keys(monthRecords.value));
  exclusionsList.value.forEach(ex => {
    const dateStr = ex.split(':')[0];
    datesToCheck.add(dateStr);
  });

  datesToCheck.forEach((dateStr) => {
    const record = monthRecords.value[dateStr] || null;
    let doneCount = 0;

    // 1. 阅读（真完成 or 被免除）
    const hasReading = record && !!(record.reading_start && record.reading_end);
    if (hasReading || isExcluded(dateStr, 'reading')) doneCount++;

    // 2. 数学（真完成 or 被免除）
    const hasMath = record && !!(
      record.math_title &&
      (record.math_min || record.math_min === 0) &&
      (record.math_sec || record.math_sec === 0)
    );
    if (hasMath || isExcluded(dateStr, 'math')) doneCount++;

    // 3. 网课（真完成 or 被免除）
    const hasClass = record && !!(record.class_title && record.class_type);
    if (hasClass || isExcluded(dateStr, 'class')) doneCount++;

    // 评判颜色标志
    if (doneCount === 3) {
      fullSet.add(dateStr);    // 三项全部搞定 -> 红点
    } else if (doneCount > 0) {
      partialSet.add(dateStr); // 搞定 1~2 项 -> 蓝点
    }
  });

  recordDateSet.value = fullSet;
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

const onMonthChange = ({ year, month }) => {
  fetchMonthRecords({ year, month });
  loadExclusions(); // 换月时顺便拉取免除名单
};

const onDataChanged = (dateStr) => {
  const d = new Date(dateStr);
  fetchMonthRecords({ year: d.getFullYear(), month: d.getMonth() + 1 });
  loadExclusions(); // 数据变动时刷新免除名单
};

// 响应式宽度判断
const checkWidth = () => {
  // #ifdef H5
  const width = window.innerWidth || document.documentElement?.clientWidth || 0;
  isWide.value = width >= 1024;
  return;
  // #endif

  isWide.value = false;
};

onMounted(() => {
  checkWidth();
  // #ifdef H5
  window.addEventListener("resize", checkWidth);
  // #endif

  // === 监听弹窗组件操作完成后的刷新信号 ===
  uni.$on('refreshCalendar', () => {
    const now = selectedDate.value;
    fetchMonthRecords({ year: now.getFullYear(), month: now.getMonth() + 1 });
    loadExclusions();
  });

  const now = new Date();
  fetchMonthRecords({ year: now.getFullYear(), month: now.getMonth() + 1 });
  loadExclusions();
});

onUnmounted(() => {
  // #ifdef H5
  window.removeEventListener("resize", checkWidth);
  // #endif
  uni.$off('refreshCalendar');
});
</script>

<style lang="scss" scoped>
.page-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f7f7f7;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;

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
  z-index: 10;
}

.desktop-title {
  font-size: 22px;
  font-weight: 700;
  color: #222;
}

.desktop-content {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 20px 24px;
  box-sizing: border-box;
  overflow: hidden;
  min-height: 0;
}

.calendar-section {
  flex: 1;
  min-width: 0;
  display: flex;
  overflow: hidden;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.entry-section {
  flex: 0 0 clamp(320px, 24vw, 430px);
  min-width: 300px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.entry-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 窄屏（手机）样式完全保留 */
.mobile-layout {
  height: 100vh;
  overflow: hidden;
}
.wrapper {
  height: 100vh;
  background: #f7f7f7;
  padding: 20rpx;
  box-sizing: border-box;
}

/* #ifdef MP-WEIXIN */
.wrapper {
  padding-bottom: calc(10rpx + constant(safe-area-inset-bottom));
  padding-bottom: calc(10rpx + env(safe-area-inset-bottom));
}
/* #endif */

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
</style>
