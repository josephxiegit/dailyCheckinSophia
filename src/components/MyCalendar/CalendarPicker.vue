<template>
  <view class="calendar-container" :class="{ 'wide-calendar': wide }">
    <view class="header" :style="headerStyle">
      <view class="month-selector">
        <u-icon name="arrow-left" @click="changeMonth(-1)"></u-icon>
        <text class="current-month">{{ currentYear }}年{{ currentMonth }}月</text>
        <u-icon name="arrow-right" @click="changeMonth(1)"></u-icon>
      </view>
      <view class="today-btn" @click="goToday">回到当天</view>
    </view>

    <view class="weekdays">
      <text v-for="day in ['日','一','二','三','四','五','六']" :key="day" class="weekday-item">{{ day }}</text>
    </view>

    <view class="days-grid">
      <view
        v-for="(item, index) in calendarDays"
        :key="index"
        class="day-cell"
        :class="{
          'other-month': !item.isCurrentMonth,
          'is-today':    item.isToday,
          'is-selected': isSameDay(item.date, props.modelValue)
        }"
        @click="selectDate(item)"
      >
        <view class="day-number">{{ item.day }}</view>
        <view v-if="item.holidayStatus === 'rest' && item.isCurrentMonth" class="rest-tag">休</view>
        <view v-if="item.holidayStatus === 'work' && item.isCurrentMonth" class="work-tag">上学</view>

        <!-- 部分完成显示蓝点，否则完全完成显示红点 -->
        <view v-if="item.isPartial && item.isCurrentMonth" class="partial-dot"></view>
        <view v-else-if="item.hasRecord && item.isCurrentMonth" class="record-dot"></view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';

const props = defineProps({
  modelValue:  { type: Date, required: true },
  recordDates: { type: Object, default: () => new Set() },
  partialDates: { type: Set, default: () => new Set() },   // 新增：部分完成日期
  wide:        { type: Boolean, default: false }           // 新增：宽屏标记
});
const emit = defineEmits(['update:modelValue', 'month-change']);

const displayDate  = ref(new Date());
const holidayDict  = ref({});

const currentYear  = computed(() => displayDate.value.getFullYear());
const currentMonth = computed(() => displayDate.value.getMonth() + 1);
const headerStyle = ref({});

const isSameDay = (d1, d2) => {
  if (!d1 || !d2) return false;
  return d1.getFullYear() === d2.getFullYear()
      && d1.getMonth()    === d2.getMonth()
      && d1.getDate()     === d2.getDate();
};

const formatDate = (date) => {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

const createDayObject = (date, isCurrentMonth) => {
  const ds = formatDate(date);
  return {
    date,
    day: date.getDate(),
    isCurrentMonth,
    isToday:       isSameDay(date, new Date()),
    holidayStatus: holidayDict.value[ds] || null,
    hasRecord:     props.recordDates.has(ds),
    isPartial:     props.partialDates.has(ds)    // 新增
  };
};

const calendarDays = computed(() => {
  const year  = currentYear.value;
  const month = displayDate.value.getMonth();
  const days  = [];
  const firstDay     = new Date(year, month, 1).getDay();
  const daysInMonth  = new Date(year, month + 1, 0).getDate();
  const daysInPrev   = new Date(year, month, 0).getDate();

  for (let i = firstDay - 1; i >= 0; i--)
    days.push(createDayObject(new Date(year, month - 1, daysInPrev - i), false));
  for (let i = 1; i <= daysInMonth; i++)
    days.push(createDayObject(new Date(year, month, i), true));
  for (let i = 1; i <= 42 - days.length; i++)
    days.push(createDayObject(new Date(year, month + 1, i), false));

  return days;
});

const changeMonth = (offset) => {
  displayDate.value = new Date(
    displayDate.value.getFullYear(),
    displayDate.value.getMonth() + offset,
    1
  );
};

const selectDate = (item) => {
  if (!item.isCurrentMonth)
    displayDate.value = new Date(item.date.getFullYear(), item.date.getMonth(), 1);
  emit('update:modelValue', item.date);
};

const goToday = () => {
  const today = new Date();
  displayDate.value = today;
  emit('update:modelValue', today);
};

// 切换月份时通知父组件去拉数据
watch([currentYear, currentMonth], ([year, month]) => {
  emit('month-change', { year, month });
});

const HOLIDAY_DATA = {
  // 2026年
  '2026-01-01': 'rest', '2026-01-02': 'rest',
  '2026-02-17': 'rest', '2026-02-18': 'rest', '2026-02-19': 'rest',
  '2026-02-20': 'rest', '2026-02-21': 'rest', '2026-02-22': 'rest',
  '2026-02-23': 'rest', '2026-02-28': 'work', '2026-03-01': 'work',
  '2026-04-03': 'rest', '2026-04-04': 'rest', '2026-04-05': 'rest',
  '2026-04-06': 'work',
  '2026-05-01': 'rest', '2026-05-02': 'rest', '2026-05-03': 'rest',
  '2026-05-04': 'rest', '2026-05-05': 'rest', '2026-05-09': 'work',
  '2026-06-19': 'rest', '2026-06-20': 'rest', '2026-06-21': 'rest',
  '2026-09-26': 'rest', '2026-09-27': 'rest',
  '2026-10-01': 'rest', '2026-10-02': 'rest', '2026-10-03': 'rest',
  '2026-10-04': 'rest', '2026-10-05': 'rest', '2026-10-06': 'rest',
  '2026-10-07': 'rest', '2026-10-10': 'work',
  // 2025年（切换到去年月份时用）
  '2025-01-01': 'rest',
  '2025-01-28': 'rest', '2025-01-29': 'rest', '2025-01-30': 'rest',
  '2025-01-31': 'rest', '2025-02-01': 'rest', '2025-02-02': 'rest',
  '2025-02-03': 'rest', '2025-02-04': 'rest', '2025-01-26': 'work',
  '2025-02-08': 'work',
  '2025-04-04': 'rest', '2025-04-05': 'rest', '2025-04-06': 'rest',
  '2025-04-27': 'work',
  '2025-05-01': 'rest', '2025-05-02': 'rest', '2025-05-03': 'rest',
  '2025-05-04': 'rest', '2025-05-05': 'rest',
  '2025-05-31': 'rest', '2025-06-01': 'rest', '2025-06-02': 'rest',
  '2025-09-28': 'work',
  '2025-10-01': 'rest', '2025-10-02': 'rest', '2025-10-03': 'rest',
  '2025-10-04': 'rest', '2025-10-05': 'rest', '2025-10-06': 'rest',
  '2025-10-07': 'rest', '2025-10-11': 'work',
};

onMounted(() => {
  holidayDict.value = HOLIDAY_DATA;
  const systemInfo = typeof uni.getSystemInfoSync === 'function'
    ? uni.getSystemInfoSync()
    : {};
  const menuButton = typeof uni.getMenuButtonBoundingClientRect === 'function'
    ? uni.getMenuButtonBoundingClientRect()
    : null;

  if (menuButton && systemInfo.windowWidth) {
    const capsuleRightGap = systemInfo.windowWidth - menuButton.right;
    const paddingRight = menuButton.width + capsuleRightGap * 2;
    headerStyle.value = { paddingRight: `${paddingRight}px` };
  } else {
    headerStyle.value = {};
  }
});
</script>

<style lang="scss" scoped>
.calendar-container { padding: 20rpx; padding-top: calc(var(--status-bar-height) + 20rpx); background: #fff; border-radius: 24rpx; }
.header { display: flex; justify-content: space-between; padding: 20rpx; }
.month-selector { display: flex; align-items: center; gap: 20rpx; font-weight: bold; }
.today-btn {
  color: #FF2D55; font-size: 24rpx;
  background: #fff1f2; padding: 8rpx 20rpx; border-radius: 20rpx;
}
.weekdays {
  display: grid; grid-template-columns: repeat(7, 1fr);
  text-align: center; color: #999; font-size: 24rpx; padding: 20rpx 0;
}
.days-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10rpx; }
.day-cell {
  height: 90rpx; display: flex; align-items: center; justify-content: center;
  position: relative; border-radius: 12rpx;
  &.other-month { color: #ccc; }
  &.is-today    { color: #FF2D55; font-weight: bold; }
  &.is-selected { background: #FF2D55; color: #fff; }
}
.rest-tag {
  position: absolute; top: 5rpx; right: 5rpx;
  font-size: 18rpx; color: #FF2D55;
  .is-selected & { color: #fff; }
}
.record-dot {
  position: absolute; bottom: 8rpx; left: 50%; transform: translateX(-50%);
  width: 10rpx; height: 10rpx; border-radius: 50%; background: #FF2D55;
  .is-selected & { background: #fff; }
}
.work-tag {
  position: absolute; top: 5rpx; right: 5rpx;
  font-size: 18rpx; color: #FF9500;
  .is-selected & { color: #fff; }
}

/* 部分完成蓝色圆点 */
.partial-dot {
  position: absolute; bottom: 8rpx; left: 50%; transform: translateX(-50%);
  width: 10rpx; height: 10rpx; border-radius: 50%; background: #007AFF;
  .is-selected & { background: #fff; }
}

/* 宽屏日历放大 */
.wide-calendar {
  width: 100%;
  height: 100%;
  padding: 28px 30px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;

  .header {
    padding: 0 0 22px;
    flex-shrink: 0;
  }

  .current-month {
    font-size: 28px;
  }

  .today-btn {
    font-size: 15px;
    padding: 8px 18px;
  }

  .days-grid {
    flex: 1;
    min-height: 0;
    gap: 12px;
  }

  .day-cell {
    height: auto;
    min-height: clamp(72px, 8.2vw, 128px);
    border-radius: 12px;
    font-size: clamp(22px, 2vw, 32px);
  }

  .weekdays {
    font-size: 15px;
    padding: 0 0 14px;
    flex-shrink: 0;
  }

  .rest-tag,
  .work-tag {
    top: 8px;
    right: 8px;
    font-size: 13px;
  }

  .record-dot,
  .partial-dot {
    width: 8px;
    height: 8px;
    bottom: 10px;
  }
}
</style>
