<template>
  <view>
    <!-- 入口按钮 -->
    <view class="viewer-btn" @click="openPicker">
      <text class="viewer-btn-text">📋 查看区间记录</text>
    </view>

    <!-- 日期选择弹窗 -->
    <view v-if="showPicker" class="overlay" @click.self="showPicker = false">
      <view class="popup-box" @click.stop>
        <view class="popup-title">选择日期范围</view>

        <view class="date-row">
          <text class="date-label">开始日期</text>
          <picker
            mode="date"
            :value="startDate"
            @change="(e) => (startDate = e.detail.value)"
          >
            <view class="date-value">{{ startDate || "请选择" }}</view>
          </picker>
        </view>

        <view class="date-row">
          <text class="date-label">结束日期</text>
          <picker
            mode="date"
            :value="endDate"
            @change="(e) => (endDate = e.detail.value)"
          >
            <view class="date-value">{{ endDate || "请选择" }}</view>
          </picker>
        </view>

        <!-- 已保存的常用日期 -->
        <view
          v-if="savedStart && savedEnd"
          class="saved-row"
          @click="useSavedAndFetch"
        >
          <view class="saved-info">
            <text class="saved-label">⭐ 常用：</text>
            <text class="saved-dates">{{ savedStart }} 至 {{ savedEnd }}</text>
          </view>
          <view class="saved-btn-quick">直接查询</view>
        </view>

        <view class="btn-row">
          <view class="btn-cancel" @click="showPicker = false">取消</view>
          <view class="btn-save" @click="saveAndFetch">
            <text v-if="!loading">保存并查询</text>
            <text v-else>查询中...</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 结果列表弹窗 -->
    <view v-if="showResult" class="overlay" @click.self="showResult = false">
      <view class="popup-box result-box" @click.stop>
        <view class="popup-title">
          <text>{{ startDate }} 至 {{ endDate }}</text>
          <text class="result-count">共 {{ records.length }} 天</text>
        </view>
        <view class="stat-row">
          <view class="stat-item done">
            <text class="stat-num">{{ totalDone }}</text>
            <text class="stat-label">已完成项</text>
          </view>
          <view class="stat-divider"></view>
          <view class="stat-item missed">
            <text class="stat-num">{{ totalMissed }}</text>
            <text class="stat-label">未录入项</text>
          </view>
        </view>

        <scroll-view scroll-y style="height: 55vh">
          <view
            v-for="r in records"
            :key="r.date"
            class="record-card"
            :class="{ 'empty-card': r.isEmpty }"
          >
            <view class="record-date">
              📅 {{ r.date }}
              <text v-if="r.isEmpty" class="no-record-badge">未录入</text>
            </view>

            <view class="record-row">
              <text class="record-tag">📖 阅读</text>
              <text class="record-val" :class="{ 'empty-val': r.isEmpty }">
                {{
                  r.isEmpty
                    ? "—"
                    : `第 ${r.reading_start} - ${r.reading_end} 页`
                }}
              </text>
            </view>

            <view class="record-row">
              <text class="record-tag">🔢 数学</text>
              <text class="record-val" :class="{ 'empty-val': r.isEmpty }">
                {{
                  r.isEmpty
                    ? "—"
                    : `${r.math_title}（${r.math_min}分${r.math_sec}秒）`
                }}
              </text>
            </view>

            <view class="record-row">
              <text class="record-tag">💻 网课</text>
              <text class="record-val" :class="{ 'empty-val': r.isEmpty }">
                {{ r.isEmpty ? "—" : `${r.class_title}（${r.class_type}）` }}
              </text>
            </view>
          </view>
        </scroll-view>

        <view class="btn-row">
          <view class="btn-cancel" style="flex: 1" @click="showResult = false"
            >关闭</view
          >
          <view
            class="btn-save"
            style="flex: 1"
            @click="
              showResult = false;
              showPicker = true;
            "
            >重新选择</view
          >
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from "vue";
import Global from "@/utils/Global.js";

const showPicker = ref(false);
const showResult = ref(false);
const loading = ref(false);
const startDate = ref("");
const endDate = ref("");
const records = ref([]);
const savedStart = ref("");
const savedEnd = ref("");
const totalDone = ref(0);
const totalMissed = ref(0);

// ── 从后端加载已保存的日期 ────────────────────────────────
const loadSavedDateRange = () => {
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: { method: "getSavedDateRange" },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
      if (res.data?.code === 0) {
        savedStart.value = res.data.startDate || "";
        savedEnd.value = res.data.endDate || "";
      }
    },
  });
};

const openPicker = () => {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  startDate.value = savedStart.value || `${y}-${m}-01`;
  endDate.value = savedEnd.value || `${y}-${m}-${d}`;
  showPicker.value = true;
};

// ── 保存到后端并查询 ──────────────────────────────────────
const saveAndFetch = () => {
  if (!startDate.value || !endDate.value)
    return uni.showToast({ title: "请选择日期范围", icon: "none" });
  if (startDate.value > endDate.value)
    return uni.showToast({ title: "开始日期不能晚于结束日期", icon: "none" });

  // 先保存到后端
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: {
      method: "saveDateRange",
      startDate: startDate.value,
      endDate: endDate.value,
    },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
      if (res.data?.code === 0) {
        savedStart.value = startDate.value;
        savedEnd.value = endDate.value;
      }
    },
  });

  fetchRecords();
};

// ── 直接用已保存日期查询 ──────────────────────────────────
const useSavedAndFetch = () => {
  startDate.value = savedStart.value;
  endDate.value = savedEnd.value;
  fetchRecords();
};

const fetchRecords = () => {
  loading.value = true;
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: {
      method: "getDateRangeRecords",
      startDate: startDate.value,
      endDate: endDate.value,
    },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
      if (res.data?.code === 0) {
        const existingMap = {};
        (res.data.data || []).forEach((r) => {
          existingMap[r.date] = r;
        });

        // 生成完整日期列表，有数据用数据，没数据标记为空
        const fullList = [];
        const cur = new Date(startDate.value);
        const end = new Date(endDate.value);
        while (cur <= end) {
          const dateStr = cur.toISOString().split("T")[0];
          fullList.push(
            existingMap[dateStr] || { date: dateStr, isEmpty: true }
          );
          cur.setDate(cur.getDate() + 1);
        }

        records.value = fullList;
        showPicker.value = false;
        showResult.value = true;
        // 统计已完成和漏掉的项数（每天3项）
        let doneCount = 0;
        let missedCount = 0;
        fullList.forEach((r) => {
          if (r.isEmpty) {
            missedCount += 3;
          } else {
            if (r.reading_start && r.reading_end) doneCount++;
            else missedCount++;
            if (r.math_title) doneCount++;
            else missedCount++;
            if (r.class_title) doneCount++;
            else missedCount++;
          }
        });
        totalDone.value = doneCount;
        totalMissed.value = missedCount;
      } else {
        uni.showToast({ title: res.data?.msg || "查询失败", icon: "none" });
      }
    },
    fail: () => uni.showToast({ title: "无法连接服务器", icon: "none" }),
    complete: () => {
      loading.value = false;
    },
  });
};

onMounted(() => loadSavedDateRange());
</script>

<style lang="scss" scoped>
.viewer-btn {
  background: #fff;
  border-radius: 20rpx;
  padding: 28rpx 30rpx;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.03);
}
.viewer-btn-text {
  font-size: 30rpx;
  color: #ff2d55;
  font-weight: bold;
}

.overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  display: flex;
  align-items: flex-end;
}
.popup-box {
  width: 100%;
  background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  padding: 40rpx 30rpx 60rpx;
  box-sizing: border-box;
}
.result-box {
  /* 删掉原来的 max-height，改用固定撑开 */
  display: flex;
  flex-direction: column;
}

.record-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 28rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}
.empty-card {
  background: #fafafa;
  border: 1rpx dashed #e0e0e0;
  box-shadow: none;
}

.record-date {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}
.no-record-badge {
  font-size: 22rpx;
  color: #fff;
  background: #ccc;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
  font-weight: normal;
}

.record-row {
  display: flex;
  gap: 16rpx;
  margin-bottom: 14rpx;
  align-items: flex-start;
}
.record-tag {
  font-size: 26rpx;
  color: #999;
  white-space: nowrap;
  min-width: 100rpx;
}
.record-val {
  font-size: 26rpx;
  color: #333;
  flex: 1;
}
.empty-val {
  color: #ccc;
}

.popup-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 40rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.result-count {
  font-size: 24rpx;
  color: #999;
  font-weight: normal;
}

.date-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}
.date-label {
  font-size: 30rpx;
  color: #333;
}
.date-value {
  font-size: 30rpx;
  color: #ff2d55;
}

.saved-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 30rpx;
  padding: 24rpx 28rpx;
  background: #fff8f0;
  border-radius: 16rpx;
  border: 1rpx solid #ffe0b2;
}
.saved-info {
  display: flex;
  align-items: center;
  gap: 10rpx;
  flex: 1;
}
.saved-label {
  font-size: 26rpx;
  color: #ff9500;
  white-space: nowrap;
}
.saved-dates {
  font-size: 24rpx;
  color: #666;
}
.saved-btn-quick {
  font-size: 26rpx;
  color: #fff;
  background: #ff9500;
  padding: 12rpx 24rpx;
  border-radius: 30rpx;
  white-space: nowrap;
}

.btn-row {
  display: flex;
  gap: 20rpx;
  margin-top: 40rpx;
}
.btn-cancel {
  flex: 1;
  height: 88rpx;
  border-radius: 50rpx;
  border: 1rpx solid #ddd;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  color: #666;
}
.btn-save {
  flex: 1;
  height: 88rpx;
  border-radius: 50rpx;
  background: #ff2d55;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  color: #fff;
}

.result-scroll {
  flex: 1;
  overflow: hidden;
}
.empty-tip {
  text-align: center;
  color: #999;
  font-size: 28rpx;
  padding: 80rpx 0;
}
.record-card {
  background: #f9f9f9;
  border-radius: 16rpx;
  padding: 28rpx;
  margin-bottom: 20rpx;
}
.record-date {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 16rpx;
}
.record-row {
  display: flex;
  gap: 16rpx;
  margin-bottom: 10rpx;
}
.record-tag {
  font-size: 26rpx;
  color: #999;
  white-space: nowrap;
}
.record-val {
  font-size: 26rpx;
  color: #333;
  flex: 1;
}

.stat-row {
  display: flex; align-items: center;
  background: #f9f9f9; border-radius: 16rpx;
  padding: 24rpx 0; margin-bottom: 30rpx;
}
.stat-item {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; gap: 8rpx;
}
.stat-num {
  font-size: 48rpx; font-weight: bold; line-height: 1;
  &.done   { color: #FF2D55; }  /* 继承父级 .done */
}
.stat-item.done   .stat-num { color: #FF2D55; }
.stat-item.missed .stat-num { color: #ccc; }
.stat-label { font-size: 24rpx; color: #999; }
.stat-divider {
  width: 1rpx; height: 60rpx; background: #e0e0e0;
}
</style>