<template>
  <view>
    <transition name="modal-anim">
      <view v-if="showPicker" class="overlay" :class="{'wide-overlay': isWide}" @click="showPicker = false">
        <view class="popup-box" :class="[isWide ? 'drawer-left' : 'popup-bottom', 'range-picker-box']" @click.stop>
          
          <view class="popup-title">选择日期范围</view>

          <view class="date-row">
            <text class="date-label">开始日期</text>
            <picker mode="date" :value="startDate" @change="(e) => (startDate = e.detail.value)">
              <view class="date-value">{{ startDate || "请选择" }}</view>
            </picker>
          </view>

          <view class="date-row">
            <text class="date-label">结束日期</text>
            <picker mode="date" :value="endDate" @change="(e) => (endDate = e.detail.value)">
              <view class="date-value">{{ endDate || "请选择" }}</view>
            </picker>
          </view>

          <view
            v-if="savedStart && savedEnd"
            class="saved-row"
            @click="onSavedRowClick"
            @touchstart="onSavedRowTouchStart"
            @touchend="onSavedRowTouchEnd"
          >
            <view class="saved-info">
              <view class="saved-main">
                <text class="saved-label">⭐ 常用：</text>
                <text class="saved-dates">{{ savedStart }} 至 {{ savedEnd }}</text>
              </view>
              <view v-if="savedAmountDisplay || savedStatusLabel" class="saved-meta">
                <text v-if="savedAmountDisplay" class="saved-meta-text">金额：{{ savedAmountDisplay }}</text>
                <text v-if="savedStatusLabel" class="saved-status" :class="savedStatusClass">{{ savedStatusLabel }}</text>
              </view>
            </view>
            <view class="saved-btn-quick">直接查询</view>
          </view>

          <view class="btn-row">
            <view class="btn-cancel" @click="showPicker = false">取消</view>
            <view class="btn-save" @click="saveAndFetch">保存并选择免除项</view>
          </view>

        </view>
      </view>
    </transition>

    <transition name="modal-anim">
      <view v-if="showExclusionPicker" class="overlay" :class="{'wide-overlay': isWide}" @click="showExclusionPicker = false">
        <view class="popup-box" :class="isWide ? 'drawer-left' : 'popup-bottom'" @click.stop>
          <view class="popup-title" style="margin-bottom: 10rpx;">配置无需打卡项目</view>
          <view style="font-size: 24rpx; color: #999; margin-bottom: 30rpx;">点绿的项目将被免除，不再计入“未录入”统计</view>
          
          <scroll-view scroll-y class="dynamic-scroll">
            <view class="ex-date-item" v-for="d in rangeDates" :key="d">
              <view class="ex-date-title">📅 {{ d }}</view>
              <view class="ex-tags">
                <view class="ex-tag" :class="{'ex-tag-active': isExcluded(d, 'reading')}" @click="toggleExclude(d, 'reading')">📖 阅读</view>
                <view class="ex-tag" :class="{'ex-tag-active': isExcluded(d, 'math')}" @click="toggleExclude(d, 'math')">🔢 数学</view>
                <view class="ex-tag" :class="{'ex-tag-active': isExcluded(d, 'class')}" @click="toggleExclude(d, 'class')">💻 网课</view>
              </view>
            </view>
          </scroll-view>

          <view class="btn-row">
            <view class="btn-cancel" style="flex: 1" @click="showExclusionPicker = false; showPicker = true;">上一步</view>
            <view class="btn-save" style="flex: 1" @click="confirmExclusionsAndFetch">
              <text v-if="!loading">确定并查询</text>
              <text v-else>查询中...</text>
            </view>
          </view>
        </view>
      </view>
    </transition>

    <transition name="modal-anim">
      <view v-if="showResult" class="overlay" :class="{'wide-overlay': isWide}" @click="showResult = false">
        <view class="popup-box result-box" :class="isWide ? 'drawer-left result-drawer-left' : 'popup-bottom'" @click.stop>
          
          <view class="popup-title">
            <text class="result-title-range">{{ startDate }} 至 {{ endDate }}</text>
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
            <view class="stat-divider"></view>
            <view class="stat-item excluded">
              <text class="stat-num">{{ totalExcluded }}</text>
              <text class="stat-label">已免除项</text>
            </view>
          </view>

          <scroll-view scroll-y class="dynamic-scroll">
            <view
              v-for="r in records"
              :key="r.date"
              class="record-card"
              :class="{ 'empty-card': r.isEmpty }"
            >
              <view class="record-date">
                📅 {{ r.date }}
                <text
                  v-if="!hasActualRecord(r, 'reading') && !hasActualRecord(r, 'math') && !hasActualRecord(r, 'class')"
                  class="no-record-badge"
                >
                  {{ isExcludedOrExempt(r, 'reading') && isExcludedOrExempt(r, 'math') && isExcludedOrExempt(r, 'class') ? '已全免除' : '未录入' }}
                </text>
              </view>

              <view class="record-row">
                <text class="record-tag">📖 阅读</text>
                <text v-if="hasActualRecord(r, 'reading')" class="record-val">第 {{ r.reading_start }} - {{ r.reading_end }} 页</text>
                <text v-else class="record-val empty-val">
                  <text v-if="isExcludedOrExempt(r, 'reading')" style="color: #34C759;">✅ 已免除</text>
                  <text v-else>—</text>
                </text>
              </view>

              <view class="record-row">
                <text class="record-tag">🔢 数学</text>
                <text v-if="hasActualRecord(r, 'math')" class="record-val">{{ r.math_title }}（{{ r.math_min }}分{{ r.math_sec }}秒）</text>
                <text v-else class="record-val empty-val">
                  <text v-if="isExcludedOrExempt(r, 'math')" style="color: #34C759;">✅ 已免除</text>
                  <text v-else>—</text>
                </text>
              </view>

              <view class="record-row">
                <text class="record-tag">💻 网课</text>
                <text v-if="hasActualRecord(r, 'class')" class="record-val">{{ r.class_title }}（{{ r.class_type }}）</text>
                <text v-else class="record-val empty-val">
                  <text v-if="isExcludedOrExempt(r, 'class')" style="color: #34C759;">✅ 已免除</text>
                  <text v-else>—</text>
                </text>
              </view>
            </view>
          </scroll-view>

          <view class="btn-row">
            <view class="btn-cancel" style="flex: 1" @click="showResult = false">关闭</view>
            <view class="btn-save" style="flex: 1" @click="onReselectClick">重新选择</view>
          </view>

        </view>
      </view>
    </transition>

    <transition name="modal-anim">
      <view v-if="showPwdDialog" class="overlay" style="align-items: center; justify-content: center; z-index: 1000;" @click="closePwdDialog">
        <view class="pwd-box" @click.stop>
          <view class="pwd-title">安全验证</view>
          <input class="pwd-input" type="password" placeholder="请输入密码" v-model="pwdInput" />
          <view class="btn-row" style="margin-top: 40rpx;">
            <view class="btn-cancel" @click="closePwdDialog">取消</view>
            <view class="btn-save" @click="verifyPwd">确认</view>
          </view>
        </view>
      </view>
    </transition>

    <transition name="modal-anim">
      <view v-if="showRewardDialog" class="overlay" style="align-items: center; justify-content: center; z-index: 1000;" @click="closeRewardDialog">
        <view class="reward-box" @click.stop>
          <view class="pwd-title">添加金额信息</view>

          <view class="reward-field">
            <text class="reward-label">金额</text>
            <input
              class="reward-input"
              type="digit"
              placeholder="请输入金额"
              v-model="rewardAmountInput"
            />
          </view>

          <view class="reward-field">
            <text class="reward-label">状态</text>
            <view class="reward-status-group">
              <view
                class="reward-status-option"
                :class="{ 'reward-status-option-active': rewardStatusInput === 'pending' }"
                @click="rewardStatusInput = 'pending'"
              >
                待领取
              </view>
              <view
                class="reward-status-option"
                :class="{ 'reward-status-option-active': rewardStatusInput === 'received' }"
                @click="rewardStatusInput = 'received'"
              >
                已领取
              </view>
            </view>
          </view>

          <view class="btn-row" style="margin-top: 40rpx;">
            <view class="btn-cancel" @click="closeRewardDialog">取消</view>
            <view class="btn-delete" @click="deleteRewardMeta">删除</view>
            <view class="btn-save" @click="confirmRewardSave">确定</view>
          </view>
        </view>
      </view>
    </transition>

  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import Global from "@/utils/Global.js";

const isWide = ref(false);
const checkWidth = () => {
  // #ifdef H5
  const width = window.innerWidth || document.documentElement?.clientWidth || 0;
  isWide.value = width >= 1024;
  return;
  // #endif
  isWide.value = false;
};

const showPicker = ref(false);
const showExclusionPicker = ref(false); 
const showResult = ref(false);
const loading = ref(false);
const startDate = ref("");
const endDate = ref("");
const records = ref([]);
const savedStart = ref("");
const savedEnd = ref("");
const savedAmount = ref("");
const savedStatus = ref("");
const totalDone = ref(0);
const totalMissed = ref(0);
const totalExcluded = ref(0);

const rangeDates = ref([]); 
const exclusionsList = ref([]); 

// === 密码验证逻辑 ===
const showPwdDialog = ref(false);
const pwdInput = ref("");
const showRewardDialog = ref(false);
const rewardAmountInput = ref("");
const rewardStatusInput = ref("pending");
const touchStartX = ref(0);
const touchStartY = ref(0);
const suppressSavedRowClick = ref(false);
let pwdSuccessCallback = null;

const savedAmountDisplay = computed(() => {
  if (savedAmount.value === "" || savedAmount.value === null || savedAmount.value === undefined) return "";
  return `${savedAmount.value}`;
});

const savedStatusLabel = computed(() => {
  if (savedStatus.value === "pending") return "待领取";
  if (savedStatus.value === "received") return "已领取";
  return "";
});

const savedStatusClass = computed(() => {
  if (savedStatus.value === "received") return "saved-status-received";
  if (savedStatus.value === "pending") return "saved-status-pending";
  return "";
});

const requirePassword = (callback) => {
  pwdInput.value = ""; 
  pwdSuccessCallback = callback;
  showPwdDialog.value = true;
};

const closePwdDialog = () => {
  showPwdDialog.value = false;
  pwdSuccessCallback = null;
};

const closeRewardDialog = () => {
  showRewardDialog.value = false;
};

const verifyPwd = () => {
  if (pwdInput.value === "ss138838") {
    showPwdDialog.value = false;
    if (pwdSuccessCallback) {
      pwdSuccessCallback();
      pwdSuccessCallback = null;
    }
  } else {
    uni.showToast({ title: "密码错误", icon: "none" });
  }
};
// ====================

const loadExclusions = (callback) => {
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: { method: "getExclusions" },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
      if (res.data?.code === 0) {
        exclusionsList.value = res.data.exclusions || [];
      }
      if (callback) callback();
    },
  });
};

const isExcluded = (date, section) => exclusionsList.value.includes(`${date}:${section}`);

const isCouponExempt = (record, section) => {
  if (!record) return false;
  if (section === "reading") return String(record.reading_start) === "-1" && String(record.reading_end) === "-1";
  if (section === "math") return record.math_title === "媛媛免除";
  if (section === "class") return record.class_title === "媛媛免除";
  return false;
};

const isExcludedOrExempt = (record, section) => {
  if (!record) return false;
  return isExcluded(record.date, section) || isCouponExempt(record, section);
};

const hasActualRecord = (record, section) => {
  if (!record || isCouponExempt(record, section)) return false;
  if (section === "reading") return !!(record.reading_start || record.reading_start === 0) && !!(record.reading_end || record.reading_end === 0);
  if (section === "math") return !!record.math_title;
  if (section === "class") return !!record.class_title;
  return false;
};

const toggleExclude = (date, section) => {
  const key = `${date}:${section}`;
  if (exclusionsList.value.includes(key)) {
    exclusionsList.value = exclusionsList.value.filter(item => item !== key);
  } else {
    exclusionsList.value.push(key);
  }
};

const calcStats = () => {
  let doneCount = 0;
  let missedCount = 0;
  let excludedCount = 0;
  const todayStr = new Date().toISOString().split("T")[0];
  
  records.value.forEach((r) => {
    if (hasActualRecord(r, 'reading')) doneCount++;
    else if (isExcludedOrExempt(r, 'reading')) excludedCount++;
    else if (r.date <= todayStr) missedCount++;
    
    if (hasActualRecord(r, 'math')) doneCount++;
    else if (isExcludedOrExempt(r, 'math')) excludedCount++;
    else if (r.date <= todayStr) missedCount++;
    
    if (hasActualRecord(r, 'class')) doneCount++;
    else if (isExcludedOrExempt(r, 'class')) excludedCount++;
    else if (r.date <= todayStr) missedCount++;
  });
  
  totalDone.value = doneCount;
  totalMissed.value = missedCount;
  totalExcluded.value = excludedCount;
};

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
        savedAmount.value = res.data.amount ?? "";
        savedStatus.value = res.data.status || "";
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

const saveAndFetch = () => {
  if (!startDate.value || !endDate.value) return uni.showToast({ title: "请选择日期范围", icon: "none" });
  if (startDate.value > endDate.value) return uni.showToast({ title: "开始日期不能晚于结束日期", icon: "none" });

  requirePassword(() => {
    uni.request({
      url: `${Global.BASE_URL}/`,
      method: "POST",
      data: { method: "saveDateRange", startDate: startDate.value, endDate: endDate.value },
      header: { "content-type": "application/x-www-form-urlencoded" },
      success: (res) => {
        if (res.data?.code === 0) {
          savedStart.value = startDate.value;
          savedEnd.value = endDate.value;
        }
      }
    });

    const list = [];
    const cur = new Date(startDate.value);
    const end = new Date(endDate.value);
    while (cur <= end) {
      list.push(cur.toISOString().split("T")[0]);
      cur.setDate(cur.getDate() + 1);
    }
    rangeDates.value = list;

    showPicker.value = false;
    showExclusionPicker.value = true;
  });
};

const onReselectClick = () => {
  requirePassword(() => {
    showResult.value = false;
    showPicker.value = true;
  });
};

const confirmExclusionsAndFetch = () => {
  loading.value = true;
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: { method: "saveExclusions", exclusions: JSON.stringify(exclusionsList.value) },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
      if (res.data?.code === 0) {
        showExclusionPicker.value = false;
        fetchRecords(); 
      } else {
        uni.showToast({ title: res.data?.msg || "保存免除项失败", icon: "none" });
        loading.value = false;
      }
    },
    fail: () => {
      uni.showToast({ title: "网络请求异常", icon: "none" });
      loading.value = false;
    }
  });
};

const useSavedAndFetch = () => {
  startDate.value = savedStart.value;
  endDate.value = savedEnd.value;
  loading.value = true;
  loadExclusions(() => {
    fetchRecords();
  });
};

const onSavedRowClick = () => {
  if (suppressSavedRowClick.value) {
    suppressSavedRowClick.value = false;
    return;
  }
  useSavedAndFetch();
};

const onSavedRowTouchStart = (event) => {
  const touch = event.changedTouches?.[0];
  if (!touch) return;
  touchStartX.value = touch.clientX;
  touchStartY.value = touch.clientY;
};

const onSavedRowTouchEnd = (event) => {
  const touch = event.changedTouches?.[0];
  if (!touch) return;

  const deltaX = touch.clientX - touchStartX.value;
  const deltaY = Math.abs(touch.clientY - touchStartY.value);

  if (deltaX > 70 && deltaY < 35) {
    suppressSavedRowClick.value = true;
    requirePassword(() => {
      rewardAmountInput.value = savedAmount.value === "" ? "" : String(savedAmount.value);
      rewardStatusInput.value = savedStatus.value || "pending";
      showRewardDialog.value = true;
    });
  }
};

const confirmRewardSave = () => {
  if (!savedStart.value || !savedEnd.value) {
    uni.showToast({ title: "请先保存常用日期", icon: "none" });
    return;
  }

  if (rewardAmountInput.value === "" || Number.isNaN(Number(rewardAmountInput.value))) {
    uni.showToast({ title: "请输入有效金额", icon: "none" });
    return;
  }

  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: {
      method: "saveSavedDateRangeMeta",
      startDate: savedStart.value,
      endDate: savedEnd.value,
      amount: rewardAmountInput.value,
      status: rewardStatusInput.value,
    },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
      if (res.data?.code === 0) {
        savedAmount.value = rewardAmountInput.value;
        savedStatus.value = rewardStatusInput.value;
        showRewardDialog.value = false;
        uni.showToast({ title: "保存成功", icon: "success" });
      } else {
        uni.showToast({ title: res.data?.msg || "保存失败", icon: "none" });
      }
    },
    fail: () => {
      uni.showToast({ title: "网络请求异常", icon: "none" });
    },
  });
};

const deleteRewardMeta = () => {
  if (!savedStart.value || !savedEnd.value) {
    uni.showToast({ title: "请先保存常用日期", icon: "none" });
    return;
  }

  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: {
      method: "deleteSavedDateRangeMeta",
    },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
      if (res.data?.code === 0) {
        savedAmount.value = "";
        savedStatus.value = "";
        rewardAmountInput.value = "";
        rewardStatusInput.value = "pending";
        showRewardDialog.value = false;
        uni.showToast({ title: "已删除", icon: "success" });
      } else {
        uni.showToast({ title: res.data?.msg || "删除失败", icon: "none" });
      }
    },
    fail: () => {
      uni.showToast({ title: "网络请求异常", icon: "none" });
    },
  });
};

const fetchRecords = () => {
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: { method: "getDateRangeRecords", startDate: startDate.value, endDate: endDate.value },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
      if (res.data?.code === 0) {
        const existingMap = {};
        (res.data.data || []).forEach((r) => { existingMap[r.date] = r; });

        const fullList = [];
        const cur = new Date(startDate.value);
        const end = new Date(endDate.value);
        while (cur <= end) {
          const dateStr = cur.toISOString().split("T")[0];
          fullList.push(existingMap[dateStr] || { date: dateStr, isEmpty: true });
          cur.setDate(cur.getDate() + 1);
        }

        records.value = fullList;
        showPicker.value = false;
        showResult.value = true;
        
        calcStats();
      } else {
        uni.showToast({ title: res.data?.msg || "查询失败", icon: "none" });
      }
    },
    complete: () => { loading.value = false; }
  });
};

onMounted(() => {
  checkWidth(); 
  // #ifdef H5
  window.addEventListener("resize", checkWidth); 
  // #endif
  
  loadExclusions(); 
  loadSavedDateRange();
});

onUnmounted(() => {
  // #ifdef H5
  window.removeEventListener("resize", checkWidth);
  // #endif
});

// 【核心修复】必须写在 script 的最下面！
defineExpose({
  openPicker
});
</script>

<style lang="scss" scoped>
.overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); z-index: 999; display: flex; align-items: flex-end; }
.popup-box { width: 100%; background: #fff; border-radius: 32rpx 32rpx 0 0; padding: 40rpx 30rpx 60rpx; box-sizing: border-box; }
.result-box { display: flex; flex-direction: column; }
.result-box .popup-title { margin-top: 16rpx; }
.record-card { background: #fff; border-radius: 16rpx; padding: 28rpx; margin-bottom: 16rpx; box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04); }
.empty-card { background: #fafafa; border: 1rpx dashed #e0e0e0; box-shadow: none; }
.record-date { font-size: 28rpx; font-weight: bold; color: #333; margin-bottom: 20rpx; display: flex; align-items: center; gap: 12rpx; }
.no-record-badge { font-size: 22rpx; color: #fff; background: #ccc; padding: 4rpx 16rpx; border-radius: 20rpx; font-weight: normal; }
.record-row { display: flex; gap: 16rpx; margin-bottom: 14rpx; align-items: flex-start; }
.record-tag { font-size: 26rpx; color: #999; white-space: nowrap; min-width: 100rpx; }
.record-val { font-size: 26rpx; color: #333; flex: 1; }
.empty-val { color: #ccc; }
.popup-title { font-size: 32rpx; font-weight: bold; color: #333; margin-bottom: 40rpx; display: flex; justify-content: space-between; align-items: center; }
.result-title-range { min-width: 0; flex: 1; white-space: nowrap; }
.range-picker-box .popup-title { margin-top: 16rpx; }
.result-count { font-size: 24rpx; color: #999; font-weight: normal; }
.date-row { display: flex; justify-content: space-between; align-items: center; padding: 28rpx 0; border-bottom: 1rpx solid #f0f0f0; }
.date-label { font-size: 30rpx; color: #333; }
.date-value { font-size: 30rpx; color: #ff2d55; }
.saved-row { display: flex; justify-content: space-between; align-items: center; margin-top: 30rpx; padding: 24rpx 28rpx; background: #fff8f0; border-radius: 16rpx; border: 1rpx solid #ffe0b2; }
.saved-info { display: flex; flex-direction: column; gap: 12rpx; flex: 1; }
.saved-main { display: flex; align-items: center; gap: 10rpx; }
.saved-label { font-size: 26rpx; color: #ff9500; white-space: nowrap; }
.saved-dates { font-size: 24rpx; color: #666; }
.saved-meta { display: flex; align-items: center; gap: 12rpx; flex-wrap: wrap; }
.saved-meta-text { font-size: 22rpx; color: #8a5a00; }
.saved-status { font-size: 22rpx; padding: 4rpx 14rpx; border-radius: 20rpx; }
.saved-status-pending { color: #b26a00; background: #ffecbf; }
.saved-status-received { color: #1f7a45; background: #dff5e7; }
.saved-btn-quick { font-size: 26rpx; color: #fff; background: #ff9500; padding: 12rpx 24rpx; border-radius: 30rpx; white-space: nowrap; }
.btn-row { display: flex; gap: 20rpx; margin-top: 40rpx; }
.btn-cancel { flex: 1; height: 88rpx; border-radius: 50rpx; border: 1rpx solid #ddd; display: flex; align-items: center; justify-content: center; font-size: 30rpx; color: #666; }
.btn-delete { flex: 1; height: 88rpx; border-radius: 50rpx; border: 1rpx solid #ffd0d8; display: flex; align-items: center; justify-content: center; font-size: 30rpx; color: #ff5c7a; background: #fff5f7; }
.btn-save { flex: 1; height: 88rpx; border-radius: 50rpx; background: #ff2d55; display: flex; align-items: center; justify-content: center; font-size: 30rpx; color: #fff; }

.stat-row { display: flex; align-items: center; background: #f9f9f9; border-radius: 16rpx; padding: 24rpx 0; margin-bottom: 30rpx; }
.stat-item { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8rpx; }
.stat-num { font-size: 48rpx; font-weight: bold; line-height: 1; }
.stat-item.done .stat-num { color: #FF2D55; }
.stat-item.missed .stat-num { color: #ccc; }
.stat-item.excluded .stat-num { color: #34C759; }
.stat-label { font-size: 24rpx; color: #999; }
.stat-divider { width: 1rpx; height: 60rpx; background: #e0e0e0; }

.ex-date-item { padding: 24rpx 0; border-bottom: 1rpx dashed #eee; }
.ex-date-title { font-size: 28rpx; font-weight: bold; color: #333; margin-bottom: 16rpx; }
.ex-tags { display: flex; gap: 16rpx; }
.ex-tag { padding: 10rpx 24rpx; border-radius: 40rpx; font-size: 24rpx; color: #666; background: #f5f5f5; border: 1rpx solid #e0e0e0; transition: all 0.2s; }
.ex-tag-active { color: #fff; background: #34C759; border-color: #34C759; }

.dynamic-scroll { height: 55vh; }
.wide-overlay { align-items: stretch; justify-content: flex-start; }
.drawer-left { width: 420px; max-width: 85vw; height: 100vh; border-radius: 0; display: flex; flex-direction: column; overflow: hidden; }
.drawer-left.range-picker-box { width: 560px; max-width: 92vw; padding: 40px 36px 44px; }
.drawer-left.range-picker-box .popup-title { font-size: 29px; margin-top: 8px; margin-bottom: 30px; }
.drawer-left.range-picker-box .date-row { padding: 22px 0; }
.drawer-left.range-picker-box .date-label,
.drawer-left.range-picker-box .date-value { font-size: 22px; }
.drawer-left.range-picker-box .saved-row { margin-top: 24px; padding: 20px 22px; border-radius: 14px; }
.drawer-left.range-picker-box .saved-label { font-size: 18px; }
.drawer-left.range-picker-box .saved-dates { font-size: 17px; }
.drawer-left.range-picker-box .saved-meta-text,
.drawer-left.range-picker-box .saved-status { font-size: 15px; }
.drawer-left.range-picker-box .saved-btn-quick { font-size: 17px; padding: 10px 18px; }
.drawer-left.range-picker-box .btn-cancel,
.drawer-left.range-picker-box .btn-delete,
.drawer-left.range-picker-box .btn-save { height: 56px; font-size: 18px; }
.drawer-left .dynamic-scroll { flex: 1; height: 0; margin-bottom: 20rpx; }
.drawer-left .btn-row { margin-top: auto; padding-bottom: 20rpx; }
.result-drawer-left { width: 520px; max-width: 92vw; }
.result-drawer-left .popup-title { margin-top: 8px; margin-bottom: 28px; font-size: 26px; gap: 12px; }
.result-drawer-left .result-title-range { font-size: 24px; }
.result-drawer-left .result-count { flex-shrink: 0; white-space: nowrap; font-size: 16px; }
.result-drawer-left .stat-row { margin-bottom: 24px; padding: 22px 0; }
.result-drawer-left .stat-num { font-size: 42px; }
.result-drawer-left .stat-label { font-size: 16px; }
.result-drawer-left .record-card { padding: 24px; margin-bottom: 14px; border-radius: 14px; }
.result-drawer-left .record-date { font-size: 22px; margin-bottom: 16px; gap: 10px; }
.result-drawer-left .no-record-badge { font-size: 15px; padding: 4px 12px; }
.result-drawer-left .record-row { margin-bottom: 12px; gap: 12px; }
.result-drawer-left .record-tag { font-size: 18px; min-width: 76px; }
.result-drawer-left .record-val { font-size: 18px; }
.result-drawer-left .btn-cancel,
.result-drawer-left .btn-save { height: 56px; font-size: 18px; }

.popup-bottom {
  padding-bottom: calc(60rpx + constant(safe-area-inset-bottom));
  padding-bottom: calc(60rpx + env(safe-area-inset-bottom));
}
/* #ifdef MP-WEIXIN */
.popup-bottom {
  padding-bottom: calc(100rpx + constant(safe-area-inset-bottom));
  padding-bottom: calc(100rpx + env(safe-area-inset-bottom));
}
/* #endif */

.pwd-box { background: #fff; width: 80%; max-width: 600rpx; border-radius: 24rpx; padding: 50rpx 40rpx; box-sizing: border-box; box-shadow: 0 10rpx 30rpx rgba(0, 0, 0, 0.1); }
.reward-box { background: #fff; width: 84%; max-width: 680rpx; border-radius: 24rpx; padding: 50rpx 40rpx; box-sizing: border-box; box-shadow: 0 10rpx 30rpx rgba(0, 0, 0, 0.1); }
.pwd-title { font-size: 34rpx; font-weight: bold; text-align: center; margin-bottom: 40rpx; color: #333; }
.pwd-input { background: #f5f5f5; height: 88rpx; border-radius: 16rpx; padding: 0 24rpx; font-size: 30rpx; text-align: center; width: 100%; box-sizing: border-box; }
.reward-field { display: flex; flex-direction: column; gap: 18rpx; margin-bottom: 28rpx; }
.reward-label { font-size: 28rpx; color: #444; font-weight: 600; }
.reward-input { background: #f5f5f5; height: 88rpx; border-radius: 16rpx; padding: 0 24rpx; font-size: 30rpx; width: 100%; box-sizing: border-box; }
.reward-status-group { display: flex; gap: 18rpx; }
.reward-status-option { flex: 1; height: 84rpx; border-radius: 16rpx; border: 1rpx solid #ddd; display: flex; align-items: center; justify-content: center; font-size: 28rpx; color: #666; background: #fff; }
.reward-status-option-active { color: #fff; border-color: #ff9500; background: #ff9500; }

.modal-anim-enter-active { animation: fadeIn 0.3s ease forwards; }
.modal-anim-leave-active { animation: fadeOut 0.3s ease forwards; }
.modal-anim-enter-active .popup-bottom { animation: slideUpIn 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }
.modal-anim-leave-active .popup-bottom { animation: slideUpOut 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }
.modal-anim-enter-active .drawer-left { animation: slideLeftIn 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }
.modal-anim-leave-active .drawer-left { animation: slideLeftOut 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }
.modal-anim-enter-active .pwd-box { animation: popIn 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }
.modal-anim-leave-active .pwd-box { animation: popOut 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }
.modal-anim-enter-active .reward-box { animation: popIn 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }
.modal-anim-leave-active .reward-box { animation: popOut 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }

@keyframes fadeIn { 0% { opacity: 0; } 100% { opacity: 1; } }
@keyframes fadeOut { 0% { opacity: 1; } 100% { opacity: 0; } }
@keyframes slideUpIn { 0% { transform: translateY(100%); } 100% { transform: translateY(0); } }
@keyframes slideUpOut { 0% { transform: translateY(0); } 100% { transform: translateY(100%); } }
@keyframes slideLeftIn { 0% { transform: translateX(-100%); } 100% { transform: translateX(0); } }
@keyframes slideLeftOut { 0% { transform: translateX(0); } 100% { transform: translateX(-100%); } }
@keyframes popIn { 0% { transform: scale(0.9); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
@keyframes popOut { 0% { transform: scale(1); opacity: 1; } 100% { transform: scale(0.9); opacity: 0; } }
</style>
