<template>
  <view class="entry-container">
    <view v-if="showCompleteFeedback" class="complete-feedback">
      <image class="complete-image" src="/static/review_complete.jpeg" mode="widthFix" />
    </view>

    <view class="date-banner" :class="{ 'readonly-banner': !isEditable }">
      <text class="date-label">{{ formattedDate }}</text>
      <text class="edit-hint">{{ isEditable ? '✏️ 可编辑' : '👁 仅查看（只支持前天到明天）' }}</text>
    </view>

    <view class="coupon-banner">
      <text class="coupon-text">🎟️ 我的免除券：{{ remainingCoupons }} 张</text>
      <view class="coupon-actions">
        <view class="coupon-btn log" @click="openLogDialog">记录</view>
        <view class="coupon-btn add" @click="onAddCouponClick">＋ 增加</view>
      </view>
    </view>

    <view class="card" :class="{ 'card--locked': isLockedReading && !isReadingExcluded }">
      <view class="card-title"><text class="card-icon">📖</text> 英语阅读</view>
      
      <view v-if="isReadingExcluded" class="excluded-tip"><text>✅ 已免除</text></view>
      <view v-else-if="isReadingCoupon" class="coupon-tip">
        <view class="coupon-tip-main">
          <text>🎟️ 媛媛免除</text>
          <text class="revoke-btn" @click="onRevokeClick('reading')">撤销</text>
        </view>
        <text v-if="readingCouponActionTime" class="status-time">使用于 {{ readingCouponActionTime }}</text>
      </view>
      
      <block v-else>
        <view class="input-row">
          <u-input v-model="form.readingStart" placeholder="开始页码" type="number" :disabled="!isEditable || isLockedReading" :border="false" customStyle="border-bottom: 1px solid #f0f0f0;"></u-input>
          <text class="split">-</text>
          <u-input v-model="form.readingEnd" placeholder="结束页码" type="number" :disabled="!isEditable || isLockedReading" :border="false" customStyle="border-bottom: 1px solid #f0f0f0;"></u-input>
        </view>
        <view v-if="isEditable" class="card-action-wrap">
          <view class="card-action-row">
          <view v-if="isLockedReading" class="locked-action-block">
            <u-button text="编辑阅读" color="#bbbbbb" size="small" customStyle="border-radius: 40rpx; flex: 1;" @click="editingReading = true"></u-button>
            <text v-if="readingActionTime" class="status-time">保存于 {{ readingActionTime }}</text>
          </view>
          <block v-else>
            <view class="action-btn-block">
              <u-button text="保存阅读" color="#FF2D55" size="small" :loading="loadingReading" customStyle="border-radius: 40rpx; flex: 1;" @click="saveReading"></u-button>
            </view>
            <view v-if="remainingCoupons > 0" class="action-btn-block action-btn-block--split">
              <u-button text="使用免除券" color="#FF9500" plain size="small" customStyle="border-radius: 40rpx; flex: 1;" @click="useCoupon('reading')"></u-button>
            </view>
          </block>
        </view>
        </view>
      </block>
      <view v-if="!isEditable && !isReadingExcluded && !isReadingCoupon" class="block-mask" @click="onBlockedTap"></view>
    </view>

    <view class="card" :class="{ 'card--locked': isLockedMath && !isMathExcluded }">
      <view class="card-title"><text class="card-icon">🔢</text> 数学练习</view>

      <view v-if="isMathExcluded" class="excluded-tip"><text>✅ 已免除</text></view>
      <view v-else-if="isMathCoupon" class="coupon-tip">
        <view class="coupon-tip-main">
          <text>🎟️ 媛媛免除</text>
          <text class="revoke-btn" @click="onRevokeClick('math')">撤销</text>
        </view>
        <text v-if="mathCouponActionTime" class="status-time">使用于 {{ mathCouponActionTime }}</text>
      </view>
      
      <block v-else>
        <u-input v-model="form.mathTitle" placeholder="练习题目内容" :disabled="!isEditable || isLockedMath" :border="false" customStyle="border-bottom: 1px solid #f0f0f0; margin-bottom: 30rpx;"></u-input>
        <view class="time-row">
          <text class="label">时长：</text>
          <view class="time-input">
            <u-input v-model="form.mathMin" type="number" placeholder="分" :disabled="!isEditable || isLockedMath" :border="false" customStyle="border-bottom: 1px solid #f0f0f0;"></u-input>
            <text>分</text>
          </view>
          <view class="time-input">
            <u-input v-model="form.mathSec" type="number" placeholder="秒" :disabled="!isEditable || isLockedMath" :border="false" customStyle="border-bottom: 1px solid #f0f0f0;"></u-input>
            <text>秒</text>
          </view>
        </view>
        <view v-if="isEditable" class="card-action-wrap">
          <view class="card-action-row">
          <view v-if="isLockedMath" class="locked-action-block">
            <u-button text="编辑数学" color="#bbbbbb" size="small" customStyle="border-radius: 40rpx; flex: 1;" @click="editingMath = true"></u-button>
            <text v-if="mathActionTime" class="status-time">保存于 {{ mathActionTime }}</text>
          </view>
          <block v-else>
            <view class="action-btn-block">
              <u-button text="保存数学" color="#FF9500" size="small" :loading="loadingMath" customStyle="border-radius: 40rpx; flex: 1;" @click="saveMath"></u-button>
            </view>
            <view v-if="remainingCoupons > 0" class="action-btn-block action-btn-block--split">
              <u-button text="使用免除券" color="#FF9500" plain size="small" customStyle="border-radius: 40rpx; flex: 1;" @click="useCoupon('math')"></u-button>
            </view>
          </block>
        </view>
        </view>
      </block>
      <view v-if="!isEditable && !isMathExcluded && !isMathCoupon" class="block-mask" @click="onBlockedTap"></view>
    </view>

    <view class="card" :class="{ 'card--locked': isLockedClass && !isClassExcluded }">
      <view class="card-title"><text class="card-icon">💻</text> 英语网课</view>

      <view v-if="isClassExcluded" class="excluded-tip"><text>✅ 已免除</text></view>
      <view v-else-if="isClassCoupon" class="coupon-tip">
        <view class="coupon-tip-main">
          <text>🎟️ 媛媛免除</text>
          <text class="revoke-btn" @click="onRevokeClick('class')">撤销</text>
        </view>
        <text v-if="classCouponActionTime" class="status-time">使用于 {{ classCouponActionTime }}</text>
      </view>

      <block v-else>
        <u-input v-model="form.classTitle" placeholder="课程标题" :disabled="!isEditable || isLockedClass" :border="false" customStyle="border-bottom: 1px solid #f0f0f0; margin-bottom: 30rpx;"></u-input>
        <view class="radio-row">
          <u-radio-group v-model="form.classType" placement="row">
            <u-radio label="上" name="上" activeColor="#34C759" :disabled="!isEditable || isLockedClass" customStyle="margin-right: 40rpx;"></u-radio>
            <u-radio label="下" name="下" activeColor="#34C759" :disabled="!isEditable || isLockedClass" customStyle="margin-right: 40rpx;"></u-radio>
            <u-radio label="全部" name="全部" activeColor="#34C759" :disabled="!isEditable || isLockedClass"></u-radio>
          </u-radio-group>
        </view>
        <view v-if="isEditable" class="card-action-wrap">
          <view class="card-action-row">
          <view v-if="isLockedClass" class="locked-action-block">
            <u-button text="编辑网课" color="#bbbbbb" size="small" customStyle="border-radius: 40rpx; flex: 1;" @click="editingClass = true"></u-button>
            <text v-if="classActionTime" class="status-time">保存于 {{ classActionTime }}</text>
          </view>
          <block v-else>
            <view class="action-btn-block">
              <u-button text="保存网课" color="#34C759" size="small" :loading="loadingClass" customStyle="border-radius: 40rpx; flex: 1;" @click="saveClass"></u-button>
            </view>
            <view v-if="remainingCoupons > 0" class="action-btn-block action-btn-block--split">
              <u-button text="使用免除券" color="#FF9500" plain size="small" customStyle="border-radius: 40rpx; flex: 1;" @click="useCoupon('class')"></u-button>
            </view>
          </block>
        </view>
        </view>
      </block>
      <view v-if="!isEditable && !isClassExcluded && !isClassCoupon" class="block-mask" @click="onBlockedTap"></view>
    </view>

    <view v-if="isEditable && hasRecord" class="delete-row">
      <u-button
        text="删除当天全部记录(含退券)"
        type="error"
        plain
        :loading="deleteLoading"
        customStyle="border-radius: 50rpx; width: 100%;"
        @click="confirmDelete"
      ></u-button>
    </view>

    <transition name="modal-anim">
      <view v-if="showPwdDialog" class="overlay" @click="closePwdDialog">
        <view class="pwd-box" @click.stop>
          <view class="pwd-title">安全验证</view>
          <input class="pwd-input" type="password" placeholder="请输入密码" v-model="pwdInput" />
          <view class="btn-row">
            <view class="btn-cancel" @click="closePwdDialog">取消</view>
            <view class="btn-save" @click="verifyPwd">确认</view>
          </view>
        </view>
      </view>
    </transition>

    <transition name="modal-anim">
      <view v-if="showAddCouponDialog" class="overlay" @click="showAddCouponDialog = false">
        <view class="pwd-box" @click.stop>
          <view class="pwd-title">发放免除券</view>
          <input class="pwd-input" type="number" placeholder="输入增加的张数" v-model="addCouponCount" />
          <view class="btn-row">
            <view class="btn-cancel" @click="showAddCouponDialog = false">取消</view>
            <view class="btn-save" @click="executeAddCoupon">确认发放</view>
          </view>
        </view>
      </view>
    </transition>

    <transition name="modal-anim">
      <view v-if="showLogDialog" class="overlay" @click="showLogDialog = false">
        <view class="log-box" @click.stop>
          <view class="pwd-title">免除券明细</view>
          <scroll-view scroll-y class="log-scroll" @scrolltolower="loadMoreLogs">
            <view class="log-item" v-for="item in logList" :key="item.id">
              <view class="log-info">
                <view class="log-detail">{{ item.detail }}</view>
                <view class="log-time">{{ item.time }}</view>
              </view>
              <view class="log-amount" :class="item.amount > 0 ? 'positive' : 'negative'">
                {{ item.amount > 0 ? '+' + item.amount : item.amount }}
              </view>
            </view>
            
            <view v-if="logList.length === 0 && !logLoading" class="empty-log">暂无记录</view>
            <view v-else-if="!hasMoreLogs && logList.length > 0" class="no-more">到底啦</view>
            <view v-else-if="logLoading" class="loading-more">加载中...</view>
          </scroll-view>
          
          <view class="btn-row" style="margin-top: 20rpx;">
            <view class="btn-cancel" style="width: 100%" @click="showLogDialog = false">关闭</view>
          </view>
        </view>
      </view>
    </transition>

  </view>
</template>

<script setup>
import { reactive, ref, computed, watch, onUnmounted } from 'vue';
import Global from '@/utils/Global.js';

const props = defineProps({
  selectedDate: { type: Date,   default: () => new Date() },
  dayRecord:    { type: Object, default: null }
});
const emit = defineEmits(['saved', 'deleted']);

const loadingReading = ref(false);
const loadingMath    = ref(false);
const loadingClass   = ref(false);
const deleteLoading  = ref(false);
const showCompleteFeedback = ref(false);
let completeFeedbackTimer = null;
let completeAudio = null;

const editingReading = ref(false);
const editingMath    = ref(false);
const editingClass   = ref(false);

const form = reactive({
  readingStart: '', readingEnd: '',
  mathTitle: '', mathMin: '', mathSec: '',
  classTitle: '', classType: ''
});

const exclusionsList = ref([]);
const remainingCoupons = ref(0);
const readingActionTime = ref("");
const mathActionTime = ref("");
const classActionTime = ref("");
const readingCouponActionTime = ref("");
const mathCouponActionTime = ref("");
const classCouponActionTime = ref("");

// 安全弹窗逻辑
const showPwdDialog = ref(false);
const pwdInput = ref("");
let pwdSuccessCallback = null;

const showAddCouponDialog = ref(false);
const addCouponCount = ref("");

// === 新增：日志弹窗数据状态 ===
const showLogDialog = ref(false);
const logList = ref([]);
const logPage = ref(1);
const logLoading = ref(false);
const hasMoreLogs = ref(true);
// =============================

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

const onAddCouponClick = () => {
  requirePassword(() => {
    addCouponCount.value = "";
    showAddCouponDialog.value = true;
  });
};

const executeAddCoupon = () => {
  const count = parseInt(addCouponCount.value);
  if (!count || count <= 0) return uni.showToast({ title: '请输入正确张数', icon: 'none' });
  
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: { method: "addCoupon", count: count },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
      if (res.data?.code === 0) {
        showAddCouponDialog.value = false;
        uni.showToast({ title: "发放成功", icon: "success" });
        loadCoupons();
      } else {
        uni.showToast({ title: res.data?.msg || "发放失败", icon: "none" }); 
      }
    },
    fail: () => uni.showToast({ title: "网络异常", icon: "none" })
  });
};

const loadCoupons = () => {
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: { method: "getCoupon" },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
      if (res.data?.code === 0) {
        remainingCoupons.value = res.data.remaining;
      }
    },
  });
};

const formatActionTime = (val) => {
  if (!val) return "";
  return val;
};

// === 新增：分页获取日志列表 ===
const fetchLogs = (isRefresh = false) => {
  if (logLoading.value || !hasMoreLogs.value) return;
  logLoading.value = true;
  
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: { method: "getCouponLogs", page: logPage.value, size: 15 },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
      if (res.data?.code === 0) {
        const newData = res.data.data || [];
        if (isRefresh) {
          logList.value = newData;
        } else {
          logList.value = [...logList.value, ...newData];
        }
        // 判断是否还有更多数据
        hasMoreLogs.value = newData.length === 15;
      }
    },
    complete: () => { logLoading.value = false; }
  });
};

const openLogDialog = () => {
  logPage.value = 1;
  hasMoreLogs.value = true;
  fetchLogs(true);
  showLogDialog.value = true;
};

const loadMoreLogs = () => {
  if (hasMoreLogs.value) {
    logPage.value += 1;
    fetchLogs(false);
  }
};
// =============================

const loadExclusions = () => {
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: "POST",
    data: { method: "getExclusions" },
    header: { "content-type": "application/x-www-form-urlencoded" },
    success: (res) => {
      if (res.data?.code === 0) {
        exclusionsList.value = res.data.exclusions || [];
      }
    },
  });
};

const isReadingExcluded = computed(() => exclusionsList.value.includes(`${formatDate(props.selectedDate)}:reading`));
const isMathExcluded = computed(() => exclusionsList.value.includes(`${formatDate(props.selectedDate)}:math`));
const isClassExcluded = computed(() => exclusionsList.value.includes(`${formatDate(props.selectedDate)}:class`));

// 媛媛免除判断
const isReadingCoupon = computed(() => String(props.dayRecord?.reading_start) === '-1');
const isMathCoupon    = computed(() => props.dayRecord?.math_title === '媛媛免除');
const isClassCoupon   = computed(() => props.dayRecord?.class_title === '媛媛免除');

const isEditable = computed(() => {
  if (!props.selectedDate) return false;
  const sel       = new Date(props.selectedDate); sel.setHours(0,0,0,0);
  const today     = new Date(); today.setHours(0,0,0,0);
  const dayBeforeYesterday = new Date(today); dayBeforeYesterday.setDate(today.getDate() - 2);
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
  const tomorrow  = new Date(today); tomorrow.setDate(today.getDate() + 1);
  return sel.getTime() === dayBeforeYesterday.getTime()
      || sel.getTime() === yesterday.getTime()
      || sel.getTime() === today.getTime()
      || sel.getTime() === tomorrow.getTime();
});

const formattedDate = computed(() => {
  const d = props.selectedDate;
  return `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日`;
});

const hasRecord = computed(() => !!props.dayRecord);
const hasReading = computed(() => !!(props.dayRecord?.reading_start));
const hasMath    = computed(() => !!(props.dayRecord?.math_title));
const hasClass   = computed(() => !!(props.dayRecord?.class_title));

const isLockedReading = computed(() => hasReading.value && !editingReading.value);
const isLockedMath    = computed(() => hasMath.value    && !editingMath.value);
const isLockedClass   = computed(() => hasClass.value   && !editingClass.value);

const formatTimeValue = (val) => {
  if (val === undefined || val === null) return '';
  const str = String(val);
  if (str === '0') return '';
  return str;
};

const populate = (record) => {
  form.readingStart = String(record?.reading_start ?? '');
  form.readingEnd   = String(record?.reading_end   ?? '');
  form.mathTitle    = record?.math_title  ?? '';
  form.mathMin = formatTimeValue(record?.math_min);
  form.mathSec = formatTimeValue(record?.math_sec);
  form.classTitle   = record?.class_title ?? '';
  form.classType    = record?.class_type  ?? '';
  readingActionTime.value = formatActionTime(record?.reading_saved_at);
  mathActionTime.value = formatActionTime(record?.math_saved_at);
  classActionTime.value = formatActionTime(record?.class_saved_at);
  readingCouponActionTime.value = formatActionTime(record?.reading_coupon_used_at);
  mathCouponActionTime.value = formatActionTime(record?.math_coupon_used_at);
  classCouponActionTime.value = formatActionTime(record?.class_coupon_used_at);
  
  editingReading.value = false;
  editingMath.value    = false;
  editingClass.value   = false;
};

watch(
  [() => props.selectedDate, () => props.dayRecord],
  ([, record]) => { 
    populate(record); 
    loadExclusions(); 
    loadCoupons();
  },
  { immediate: true }
);

const showError  = (msg) => uni.showToast({ title: msg, icon: 'none', duration: 2000 });
const getCompleteAudio = () => {
  if (completeAudio) return completeAudio;
  completeAudio = uni.createInnerAudioContext();
  completeAudio.src = '/static/success.mp3';
  return completeAudio;
};

const stopCompleteAudio = () => {
  if (!completeAudio) return;
  completeAudio.stop();
  completeAudio.seek(0);
};

const showSaveComplete = () => {
  if (completeFeedbackTimer) clearTimeout(completeFeedbackTimer);
  const audio = getCompleteAudio();
  audio.stop();
  audio.seek(0);
  audio.play();
  showCompleteFeedback.value = true;
  completeFeedbackTimer = setTimeout(() => {
    showCompleteFeedback.value = false;
    stopCompleteAudio();
    completeFeedbackTimer = null;
  }, 800);
};

const formatDate = (date) => {
  const y = date.getFullYear();
  const m = String(date.getMonth()+1).padStart(2,'0');
  const d = String(date.getDate()).padStart(2,'0');
  return `${y}-${m}-${d}`;
};

const onBlockedTap = () => {
  uni.showToast({ title: '未到日期录入', icon: 'none', duration: 2000 });
};

const validateReading = () => {
  if (!form.readingStart || !form.readingEnd) return showError('请填写英语阅读页码'), false;
  if (!/^\d+$/.test(form.readingStart) || !/^\d+$/.test(form.readingEnd)) return showError('页码必须是数字'), false;
  if (Number(form.readingEnd) <= Number(form.readingStart)) return showError('结束页码必须大于开始页码'), false;
  return true;
};

const validateMath = () => {
  if (!form.mathTitle.trim()) return showError('请填写数学练习题目'), false;
  if (form.mathMin === '' || form.mathSec === '') return showError('请填写数学练习时长'), false;
  if (!/^\d+$/.test(form.mathMin) || !/^\d+$/.test(form.mathSec)) return showError('时长必须是数字'), false;
  return true;
};

const validateClass = () => {
  if (!form.classTitle.trim()) return showError('请填写网课课程标题'), false;
  if (!form.classType) return showError('请选择网课类型'), false;
  return true;
};

const responseOk = (res) => {
  if (res.data?.code === 0) return true;
  showError(res.data?.msg || '操作失败');
  return false;
};

// 使用免除券
const useCoupon = (sectionName) => {
  uni.showModal({
    title: '确认使用',
    content: '要消耗 1 张免除券来抵消此项任务吗？',
    confirmColor: '#FF9500',
    success: (res) => {
      if (res.confirm) {
        uni.request({
          url: `${Global.BASE_URL}/`,
          method: 'POST',
          data: { method: 'useCoupon', section: sectionName, date: formatDate(props.selectedDate) },
          header: { 'content-type': 'application/x-www-form-urlencoded' },
          success: (resp) => {
            if (responseOk(resp)) {
              if (sectionName === 'reading') readingCouponActionTime.value = formatActionTime(resp.data?.actionTime);
              if (sectionName === 'math') mathCouponActionTime.value = formatActionTime(resp.data?.actionTime);
              if (sectionName === 'class') classCouponActionTime.value = formatActionTime(resp.data?.actionTime);
              showSaveComplete();
              emit('saved', formatDate(props.selectedDate));
              loadCoupons();
            }
          }
        });
      }
    }
  });
};

// === 新增：撤销免除券 ===
const onRevokeClick = (sectionName) => {
  requirePassword(() => {
    uni.request({
      url: `${Global.BASE_URL}/`,
      method: 'POST',
      data: { method: 'revokeCoupon', section: sectionName, date: formatDate(props.selectedDate) },
      header: { 'content-type': 'application/x-www-form-urlencoded' },
      success: (resp) => {
        if (responseOk(resp)) {
          uni.showToast({ title: '撤销成功并退券', icon: 'none' });
          emit('saved', formatDate(props.selectedDate)); // 通知父组件刷新
          loadCoupons(); // 刷新数字
        }
      }
    });
  });
};
// =========================

const saveReading = () => {
  if (!validateReading()) return;
  loadingReading.value = true;
  uni.request({
    url: `${Global.BASE_URL}/`, method: 'POST',
    data: { method: 'saveStudyRecord', section: 'reading', date: formatDate(props.selectedDate), readingStart: form.readingStart, readingEnd: form.readingEnd },
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    success: (res) => { if (responseOk(res)) { readingActionTime.value = formatActionTime(res.data?.actionTime); showSaveComplete(); editingReading.value = false; emit('saved', formatDate(props.selectedDate)); } },
    complete: () => { loadingReading.value = false; }
  });
};

const saveMath = () => {
  if (!validateMath()) return;
  loadingMath.value = true;
  uni.request({
    url: `${Global.BASE_URL}/`, method: 'POST',
    data: { method: 'saveStudyRecord', section: 'math', date: formatDate(props.selectedDate), mathTitle: form.mathTitle, mathMin: form.mathMin, mathSec: form.mathSec },
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    success: (res) => { if (responseOk(res)) { mathActionTime.value = formatActionTime(res.data?.actionTime); showSaveComplete(); editingMath.value = false; emit('saved', formatDate(props.selectedDate)); } },
    complete: () => { loadingMath.value = false; }
  });
};

const saveClass = () => {
  if (!validateClass()) return;
  loadingClass.value = true;
  uni.request({
    url: `${Global.BASE_URL}/`, method: 'POST',
    data: { method: 'saveStudyRecord', section: 'class', date: formatDate(props.selectedDate), classTitle: form.classTitle, classType: form.classType },
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    success: (res) => { if (responseOk(res)) { classActionTime.value = formatActionTime(res.data?.actionTime); showSaveComplete(); editingClass.value = false; emit('saved', formatDate(props.selectedDate)); } },
    complete: () => { loadingClass.value = false; }
  });
};

const confirmDelete = () => {
  uni.showModal({
    title: '确认删除',
    content: '确定要删除这一天的全部学习记录吗？(若含免除券也会自动退还哦)',
    confirmColor: '#FF2D55',
    success: (res) => { if (res.confirm) executeDelete(); }
  });
};

const executeDelete = () => {
  deleteLoading.value = true;
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: 'POST',
    data: { method: 'deleteStudyRecord', date: formatDate(props.selectedDate) },
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    success: (res) => {
      if (res.data?.code === 0) {
        uni.showToast({ title: '删除并退券成功', icon: 'none' });
        populate(null);
        emit('deleted', formatDate(props.selectedDate));
        loadCoupons(); // 删除可能导致退券，所以刷新一下数字
      } else {
        showError(res.data?.msg || '删除失败');
      }
    },
    complete: () => { deleteLoading.value = false; }
  });
};

onUnmounted(() => {
  if (completeFeedbackTimer) clearTimeout(completeFeedbackTimer);
  stopCompleteAudio();
  if (completeAudio) { completeAudio.destroy(); completeAudio = null; }
});
</script>

<style lang="scss" scoped>
.entry-container { padding: 30rpx 20rpx; }

.complete-feedback {
  position: fixed; inset: 0; z-index: 9999;
  display: flex; align-items: center; justify-content: center; pointer-events: none;
}
.complete-image { width: 420rpx; max-width: 78vw; border-radius: 18rpx; box-shadow: 0 18rpx 50rpx rgba(0, 0, 0, 0.18); }

.date-banner {
  display: flex; justify-content: space-between; align-items: center;
  background: #fff1f2; border-radius: 16rpx; padding: 20rpx 30rpx; margin-bottom: 30rpx;
  .date-label { font-size: 32rpx; font-weight: bold; color: #FF2D55; }
  .edit-hint  { font-size: 22rpx; color: #FF2D55; }
  &.readonly-banner { background: #f5f5f5; .date-label, .edit-hint { color: #999; } }
}

/* === 免除券 UI 升级 === */
.coupon-banner {
  display: flex; justify-content: space-between; align-items: center;
  background: #FFFBF0; border-radius: 16rpx; padding: 20rpx 30rpx; margin-bottom: 30rpx;
  border: 1px solid #FFE0B2;
  .coupon-text { font-size: 28rpx; font-weight: bold; color: #FF9500; }
  .coupon-actions { display: flex; gap: 16rpx; }
  .coupon-btn { font-size: 24rpx; padding: 8rpx 24rpx; border-radius: 30rpx; cursor: pointer; }
  .coupon-btn.add { color: #fff; background: #FF9500; }
  .coupon-btn.log { color: #FF9500; background: #FFF3E0; border: 1px solid #FFD180; }
}

.coupon-tip {
  display: flex; flex-direction: column; gap: 12rpx;
  padding: 24rpx 40rpx; font-size: 32rpx; font-weight: bold;
  color: #FF2D55; background: #FFF1F2; border-radius: 12rpx; border: 1px dashed #FFD4D9;
}

.coupon-tip-main {
  display: flex; justify-content: space-between; align-items: center;

  .revoke-btn {
    font-size: 24rpx; font-weight: normal; color: #fff;
    background: #FF2D55; padding: 8rpx 24rpx; border-radius: 30rpx; cursor: pointer;
  }
}

.excluded-tip {
  padding: 30rpx 0; text-align: center; font-size: 32rpx; font-weight: bold;
  color: #FF9500; background: #FFF8E1; border-radius: 12rpx; border: 1px dashed #FFE0B2;
}

.card {
  position: relative; background: #fff; border-radius: 20rpx; padding: 30rpx; margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.03); transition: background 0.2s;
  .card-title { font-size: 32rpx; font-weight: bold; margin-bottom: 30rpx; color: #333; transition: color 0.2s; .card-icon { margin-right: 8rpx; transition: all 0.2s; } }
  &.card--locked { background: #f7f7f7; box-shadow: none; .card-title { color: #bbb; .card-icon { filter: grayscale(100%); opacity: 0.6; } } text, .split, .label { color: #bbb !important; } :deep(input), :deep(.u-input__content__field-wrapper__field) { color: #bbb !important; -webkit-text-fill-color: #bbb !important; } :deep(.u-radio__text) { color: #bbb !important; } }
}

.card-action-row { display: flex; }
.card-action-wrap { display: flex; flex-direction: column; gap: 12rpx; margin-top: 30rpx; }
.action-btn-block { display: flex; flex-direction: column; gap: 8rpx; flex: 1; }
.action-btn-block--split { margin-left: 20rpx; }
.locked-action-block { display: flex; flex-direction: column; gap: 8rpx; flex: 1; }
.locked-action-block :deep(.u-button) { min-height: 104rpx !important; }
.locked-action-block :deep(.u-button__text) { font-size: 30rpx !important; }
.status-time { font-size: 20rpx; color: #999; line-height: 1.2; padding-left: 10rpx; }
.input-row { display: flex; align-items: center; gap: 20rpx; .split { color: #999; } }
.time-row { display: flex; align-items: center; gap: 10rpx; font-size: 28rpx; color: #333; .time-input { display: flex; align-items: center; width: 140rpx; gap: 10rpx; } }
.radio-row { padding-top: 10rpx; }
.delete-row { margin-top: 10rpx; margin-bottom: 40rpx; }
.block-mask { position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: 10; background: transparent; }

/* 弹窗通用样式 */
.overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); z-index: 999; display: flex; align-items: center; justify-content: center; }
.pwd-box { background: #fff; width: 80%; max-width: 600rpx; border-radius: 24rpx; padding: 50rpx 40rpx; box-sizing: border-box; box-shadow: 0 10rpx 30rpx rgba(0, 0, 0, 0.1); }
.pwd-title { font-size: 34rpx; font-weight: bold; text-align: center; margin-bottom: 40rpx; color: #333; }
.pwd-input { background: #f5f5f5; height: 88rpx; border-radius: 16rpx; padding: 0 24rpx; font-size: 30rpx; text-align: center; width: 100%; box-sizing: border-box; }
.btn-row { display: flex; gap: 20rpx; margin-top: 40rpx; }
.btn-cancel { flex: 1; height: 88rpx; border-radius: 50rpx; border: 1rpx solid #ddd; display: flex; align-items: center; justify-content: center; font-size: 30rpx; color: #666; }
.btn-save { flex: 1; height: 88rpx; border-radius: 50rpx; background: #ff2d55; display: flex; align-items: center; justify-content: center; font-size: 30rpx; color: #fff; }

/* === 新增：日志列表弹窗专属样式 === */
.log-box { 
  background: #fff; width: 90%; max-width: 680rpx; border-radius: 24rpx; 
  padding: 40rpx; box-sizing: border-box; display: flex; flex-direction: column;
}
.log-scroll { height: 50vh; margin-top: 20rpx; }
.log-item { 
  display: flex; justify-content: space-between; align-items: center; 
  padding: 24rpx 0; border-bottom: 1rpx solid #f5f5f5; 
}
.log-info { display: flex; flex-direction: column; gap: 10rpx; flex: 1; padding-right: 20rpx;}
.log-detail { font-size: 28rpx; color: #333; }
.log-time { font-size: 24rpx; color: #999; }
.log-amount { font-size: 36rpx; font-weight: bold; }
.log-amount.positive { color: #FF9500; }
.log-amount.negative { color: #34C759; } /* 消耗显示绿色 */
.empty-log, .no-more { text-align: center; font-size: 24rpx; color: #ccc; padding: 30rpx 0; }
.loading-more { text-align: center; font-size: 24rpx; color: #999; padding: 20rpx 0; }
/* ================================== */

.modal-anim-enter-active { animation: fadeIn 0.3s ease forwards; }
.modal-anim-leave-active { animation: fadeOut 0.3s ease forwards; }
.modal-anim-enter-active .pwd-box, .modal-anim-enter-active .log-box { animation: popIn 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }
.modal-anim-leave-active .pwd-box, .modal-anim-leave-active .log-box { animation: popOut 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) forwards; }

@keyframes fadeIn { 0% { opacity: 0; } 100% { opacity: 1; } }
@keyframes fadeOut { 0% { opacity: 1; } 100% { opacity: 0; } }
@keyframes popIn { 0% { transform: scale(0.9); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
@keyframes popOut { 0% { transform: scale(1); opacity: 1; } 100% { transform: scale(0.9); opacity: 0; } }

@media (min-width: 1024px) {
  .entry-container { padding: 24px 10px; :deep(input), :deep(.u-input__content__field-wrapper__field), :deep(.u-radio__text), .label, .time-input text, .split { font-size: 18px !important; } .date-banner { padding: 20px 24px; .date-label { font-size: 22px; } .edit-hint { font-size: 15px; } } .card { padding: 30px; margin-bottom: 24px; .card-title { font-size: 20px; margin-bottom: 24px; .card-icon { font-size: 24px; } } } :deep(.u-button__text) { font-size: 16px !important; } .locked-action-block :deep(.u-button) { min-height: 54px !important; } .locked-action-block :deep(.u-button__text) { font-size: 18px !important; } .status-time { font-size: 14px; } }
  .complete-image { width: min(32vw, 520px); max-width: 520px; }
}
</style>
