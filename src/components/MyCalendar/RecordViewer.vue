<template>
  <view>
    <!-- 入口按钮 -->
    <view class="viewer-btn" @click="openPicker">
      <text class="viewer-btn-text">📋 查看区间记录</text>
    </view>

    <!-- 第 1 步：日期选择弹窗 -->
    <transition name="modal-anim">
      <view v-if="showPicker" class="overlay" :class="{'wide-overlay': isWide}" @click="showPicker = false">
        <view class="popup-box" :class="isWide ? 'drawer-left' : 'popup-bottom'" @click.stop>
          
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

          <view v-if="savedStart && savedEnd" class="saved-row" @click="useSavedAndFetch">
            <view class="saved-info">
              <text class="saved-label">⭐ 常用：</text>
              <text class="saved-dates">{{ savedStart }} 至 {{ savedEnd }}</text>
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

    <!-- 第 2 步：免除项选择弹窗 -->
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

    <!-- 第 3 步：结果列表弹窗 -->
    <transition name="modal-anim">
      <view v-if="showResult" class="overlay" :class="{'wide-overlay': isWide}" @click="showResult = false">
        <view class="popup-box result-box" :class="isWide ? 'drawer-left' : 'popup-bottom'" @click.stop>
          
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
                <text v-if="!r.reading_start && !r.math_title && !r.class_title" class="no-record-badge">
                  {{ (isExcluded(r.date, 'reading') && isExcluded(r.date, 'math') && isExcluded(r.date, 'class')) ? '已全免除' : '未录入' }}
                </text>
              </view>

              <view class="record-row">
                <text class="record-tag">📖 阅读</text>
                <text v-if="r.reading_start" class="record-val">第 {{ r.reading_start }} - {{ r.reading_end }} 页</text>
                <text v-else class="record-val empty-val">
                  <text v-if="isExcluded(r.date, 'reading')" style="color: #34C759;">✅ 已免除</text>
                  <text v-else>—</text>
                </text>
              </view>

              <view class="record-row">
                <text class="record-tag">🔢 数学</text>
                <text v-if="r.math_title" class="record-val">{{ r.math_title }}（{{ r.math_min }}分{{ r.math_sec }}秒）</text>
                <text v-else class="record-val empty-val">
                  <text v-if="isExcluded(r.date, 'math')" style="color: #34C759;">✅ 已免除</text>
                  <text v-else>—</text>
                </text>
              </view>

              <view class="record-row">
                <text class="record-tag">💻 网课</text>
                <text v-if="r.class_title" class="record-val">{{ r.class_title }}（{{ r.class_type }}）</text>
                <text v-else class="record-val empty-val">
                  <text v-if="isExcluded(r.date, 'class')" style="color: #34C759;">✅ 已免除</text>
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

    <!-- 密码验证弹窗 -->
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

  </view>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
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
const totalDone = ref(0);
const totalMissed = ref(0);
const totalExcluded = ref(0);

const rangeDates = ref([]); 
const exclusionsList = ref([]); 

// === 密码验证逻辑 ===
const showPwdDialog = ref(false);
const pwdInput = ref("");
let pwdSuccessCallback = null;

const requirePassword = (callback) => {
  pwdInput.value = ""; 
  pwdSuccessCallback = callback;
  showPwdDialog.value = true;
};

const closePwdDialog = () => {
  showPwdDialog.value = false;
  pwdSuccessCallback = null;
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
  
  records.value.forEach((r) => {
    if (r.reading_start) doneCount++;
    else if (isExcluded(r.date, 'reading')) excludedCount++;
    else missedCount++;
    
    if (r.math_title) doneCount++;
    else if (isExcluded(r.date, 'math')) excludedCount++;
    else missedCount++;
    
    if (r.class_title) doneCount++;
    else if (isExcluded(r.date, 'class')) excludedCount++;
    else missedCount++;
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
</script>

<style lang="scss" scoped>
/* ====================================================
   【原版基础样式】
   ==================================================== */
.viewer-btn { background: #fff; border-radius: 20rpx; padding: 28rpx 30rpx; margin-bottom: 20rpx; display: flex; align-items: center; justify-content: center; box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.03); }
.viewer-btn-text { font-size: 30rpx; color: #ff2d55; font-weight: bold; }
.overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); z-index: 999; display: flex; align-items: flex-end; }
.popup-box { width: 100%; background: #fff; border-radius: 32rpx 32rpx 0 0; padding: 40rpx 30rpx 60rpx; box-sizing: border-box; }
.result-box { display: flex; flex-direction: column; }
.record-card { background: #fff; border-radius: 16rpx; padding: 28rpx; margin-bottom: 16rpx; box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04); }
.empty-card { background: #fafafa; border: 1rpx dashed #e0e0e0; box-shadow: none; }
.record-date { font-size: 28rpx; font-weight: bold; color: #333; margin-bottom: 20rpx; display: flex; align-items: center; gap: 12rpx; }
.no-record-badge { font-size: 22rpx; color: #fff; background: #ccc; padding: 4rpx 16rpx; border-radius: 20rpx; font-weight: normal; }
.record-row { display: flex; gap: 16rpx; margin-bottom: 14rpx; align-items: flex-start; }
.record-tag { font-size: 26rpx; color: #999; white-space: nowrap; min-width: 100rpx; }
.record-val { font-size: 26rpx; color: #333; flex: 1; }
.empty-val { color: #ccc; }
.popup-title { font-size: 32rpx; font-weight: bold; color: #333; margin-bottom: 40rpx; display: flex; justify-content: space-between; align-items: center; }
.result-count { font-size: 24rpx; color: #999; font-weight: normal; }
.date-row { display: flex; justify-content: space-between; align-items: center; padding: 28rpx 0; border-bottom: 1rpx solid #f0f0f0; }
.date-label { font-size: 30rpx; color: #333; }
.date-value { font-size: 30rpx; color: #ff2d55; }
.saved-row { display: flex; justify-content: space-between; align-items: center; margin-top: 30rpx; padding: 24rpx 28rpx; background: #fff8f0; border-radius: 16rpx; border: 1rpx solid #ffe0b2; }
.saved-info { display: flex; align-items: center; gap: 10rpx; flex: 1; }
.saved-label { font-size: 26rpx; color: #ff9500; white-space: nowrap; }
.saved-dates { font-size: 24rpx; color: #666; }
.saved-btn-quick { font-size: 26rpx; color: #fff; background: #ff9500; padding: 12rpx 24rpx; border-radius: 30rpx; white-space: nowrap; }
.btn-row { display: flex; gap: 20rpx; margin-top: 40rpx; }
.btn-cancel { flex: 1; height: 88rpx; border-radius: 50rpx; border: 1rpx solid #ddd; display: flex; align-items: center; justify-content: center; font-size: 30rpx; color: #666; }
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

/* ====================================================
   【自适应宽高与安全区适配】
   ==================================================== */
.dynamic-scroll { height: 55vh; }
.wide-overlay { align-items: stretch; justify-content: flex-start; }
.drawer-left { width: 420px; max-width: 85vw; height: 100vh; border-radius: 0; display: flex; flex-direction: column; overflow: hidden; }
.drawer-left .dynamic-scroll { flex: 1; height: 0; margin-bottom: 20rpx; }
.drawer-left .btn-row { margin-top: auto; padding-bottom: 20rpx; }

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
.pwd-title { font-size: 34rpx; font-weight: bold; text-align: center; margin-bottom: 40rpx; color: #333; }
.pwd-input { background: #f5f5f5; height: 88rpx; border-radius: 16rpx; padding: 0 24rpx; font-size: 30rpx; text-align: center; width: 100%; box-sizing: border-box; }


/* ====================================================
   【核心修复】跨端完美动画（H5/小程序通用 Keyframes）
   ==================================================== */
/* 1. 遮罩层共用淡入淡出 */
.modal-anim-enter-active { animation: fadeIn 0.3s ease forwards; }
.modal-anim-leave-active { animation: fadeOut 0.3s ease forwards; }

/* 2. 手机端底部弹窗 */
.modal-anim-enter-active .popup-bottom { animation: slideUpIn 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }
.modal-anim-leave-active .popup-bottom { animation: slideUpOut 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }

/* 3. 大屏左侧抽屉 */
.modal-anim-enter-active .drawer-left { animation: slideLeftIn 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }
.modal-anim-leave-active .drawer-left { animation: slideLeftOut 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }

/* 4. 密码框居中缩放 */
.modal-anim-enter-active .pwd-box { animation: popIn 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }
.modal-anim-leave-active .pwd-box { animation: popOut 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }

@keyframes fadeIn { 0% { opacity: 0; } 100% { opacity: 1; } }
@keyframes fadeOut { 0% { opacity: 1; } 100% { opacity: 0; } }

@keyframes slideUpIn { 0% { transform: translateY(100%); } 100% { transform: translateY(0); } }
@keyframes slideUpOut { 0% { transform: translateY(0); } 100% { transform: translateY(100%); } }

@keyframes slideLeftIn { 0% { transform: translateX(-100%); } 100% { transform: translateX(0); } }
@keyframes slideLeftOut { 0% { transform: translateX(0); } 100% { transform: translateX(-100%); } }

@keyframes popIn { 0% { transform: scale(0.9); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
@keyframes popOut { 0% { transform: scale(1); opacity: 1; } 100% { transform: scale(0.9); opacity: 0; } }
</style>