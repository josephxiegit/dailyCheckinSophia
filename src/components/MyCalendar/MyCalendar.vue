<template>
  <scroll-view scroll-y class="wrapper">
    <RecordViewer /> 
    <CalendarPicker
      v-model="selectedDate"
      :record-dates="recordDateSet"
      @month-change="onMonthChange"
    />
    <InputEntry
      :selected-date="selectedDate"
      :day-record="currentDayRecord"
      @saved="onDataChanged"
      @deleted="onDataChanged"
    />
  </scroll-view>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import CalendarPicker from "./CalendarPicker.vue";
import InputEntry from "./InputEntry.vue";
import Global from "@/utils/Global.js";
import RecordViewer   from "./RecordViewer.vue";

const selectedDate    = ref(new Date());
const monthRecords    = ref({});       // { 'YYYY-MM-DD': { ... } }
const currentDayRecord = ref(null);    // ← computed 대신 ref로 변경
const recordDateSet   = ref(new Set()); // ← 마찬가지

const formatDate = (date) => {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
};

// ── monthRecords 또는 selectedDate 가 바뀔 때마다 명시적으로 갱신 ──
const syncDerivedState = () => {
  // 打卡圆点集合
  recordDateSet.value = new Set(Object.keys(monthRecords.value));
  // 当前选中日期的记录
  const key = formatDate(selectedDate.value);
  currentDayRecord.value = monthRecords.value[key] || null;

  // 调试日志：确认数据是否到位
//   console.log('[MyCalendar] monthRecords keys:', [...recordDateSet.value]);
//   console.log('[MyCalendar] selectedDate:', key, '→ record:', currentDayRecord.value);
};

watch(selectedDate,  syncDerivedState);
watch(monthRecords,  syncDerivedState, { deep: true });

// ── 拉取指定月份数据 ──────────────────────────────────────
const fetchMonthRecords = ({ year, month }) => {
//   console.log('[MyCalendar] fetchMonthRecords →', year, month);

  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: { method: "getMonthRecords", year, month },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
    //   console.log('[MyCalendar] 后端响应:', JSON.stringify(res.data));

      if (res.data?.code === 0) {
        const rawData = res.data.data || {};
        const cleanData = {};
        for (const key in rawData) {
          const cleanKey = key.split(" ")[0]; // '2026-05-11 00:00:00' → '2026-05-11'
          cleanData[cleanKey] = rawData[key];
        }
        monthRecords.value = cleanData; // 触发 watch → syncDerivedState
      } else {
        // console.error('[MyCalendar] getMonthRecords 失败:', res.data);
      }
    },
    fail: (err) => {
    //   console.error('[MyCalendar] 网络请求失败:', err);
      uni.showToast({ title: "加载记录失败", icon: "none" });
    },
  });
};

const onMonthChange  = ({ year, month }) => fetchMonthRecords({ year, month });
const onDataChanged  = (dateStr) => {
  const d = new Date(dateStr);
  fetchMonthRecords({ year: d.getFullYear(), month: d.getMonth() + 1 });
};

onMounted(() => {
  const now = new Date();
  fetchMonthRecords({ year: now.getFullYear(), month: now.getMonth() + 1 });
});
</script>

<style lang="scss" scoped>
.wrapper {
  height: 100vh;
  background: #f7f7f7;
  padding: 20rpx;
  box-sizing: border-box;
}
</style>