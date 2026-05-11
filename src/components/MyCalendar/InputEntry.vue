<template>
  <view class="entry-container">

    <view class="date-banner" :class="{ 'readonly-banner': !isEditable }">
      <text class="date-label">{{ formattedDate }}</text>
      <text class="edit-hint">{{ isEditable ? '✏️ 可编辑' : '👁 仅查看（只支持今天和昨天）' }}</text>
    </view>

<view class="card">
  <view class="card-title">📖 英语阅读</view>
  <view class="input-row">
    <u-input v-model="form.readingStart" placeholder="开始页码" type="number"
      :disabled="!isEditable" :border="false"
      customStyle="border-bottom: 1px solid #f0f0f0;"></u-input>
    <text class="split">-</text>
    <u-input v-model="form.readingEnd" placeholder="结束页码" type="number"
      :disabled="!isEditable" :border="false"
      customStyle="border-bottom: 1px solid #f0f0f0;"></u-input>
  </view>
  <!-- 不可编辑时的拦截遮罩 -->
  <view v-if="!isEditable" class="block-mask" @click="onBlockedTap"></view>
</view>

<view class="card">
  <view class="card-title">🔢 数学练习</view>
  <u-input v-model="form.mathTitle" placeholder="练习题目内容"
    :disabled="!isEditable" :border="false"
    customStyle="border-bottom: 1px solid #f0f0f0; margin-bottom: 30rpx;"></u-input>
  <view class="time-row">
    <text class="label">时长：</text>
    <view class="time-input">
      <u-input v-model="form.mathMin" type="number" placeholder="0"
        :disabled="!isEditable" :border="false"
        customStyle="border-bottom: 1px solid #f0f0f0;"></u-input>
      <text>分</text>
    </view>
    <view class="time-input">
      <u-input v-model="form.mathSec" type="number" placeholder="0"
        :disabled="!isEditable" :border="false"
        customStyle="border-bottom: 1px solid #f0f0f0;"></u-input>
      <text>秒</text>
    </view>
  </view>
  <view v-if="!isEditable" class="block-mask" @click="onBlockedTap"></view>
</view>

<view class="card">
  <view class="card-title">💻 英语网课</view>
  <u-input v-model="form.classTitle" placeholder="课程标题"
    :disabled="!isEditable" :border="false"
    customStyle="border-bottom: 1px solid #f0f0f0; margin-bottom: 30rpx;"></u-input>
  <view class="radio-row">
    <u-radio-group v-model="form.classType" placement="row">
      <u-radio label="上"   name="上"   activeColor="#FF2D55" :disabled="!isEditable" customStyle="margin-right: 40rpx;"></u-radio>
      <u-radio label="下"   name="下"   activeColor="#FF2D55" :disabled="!isEditable" customStyle="margin-right: 40rpx;"></u-radio>
      <u-radio label="全部" name="全部" activeColor="#FF2D55" :disabled="!isEditable"></u-radio>
    </u-radio-group>
  </view>
  <view v-if="!isEditable" class="block-mask" @click="onBlockedTap"></view>
</view>

    <view class="action-row" v-if="isEditable">
      <u-button
        text="保存记录"
        color="#FF2D55"
        :loading="loading"
        customStyle="flex: 1; border-radius: 50rpx; margin-right: 20rpx;"
        @click="saveData"
      ></u-button>
      
      <u-button
        v-if="hasRecord"
        text="删除"
        type="error"
        plain
        :loading="deleteLoading"
        customStyle="width: 160rpx; border-radius: 50rpx;"
        @click="confirmDelete"
      ></u-button>
    </view>

  </view>
</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue';
import Global from '@/utils/Global.js';

const props = defineProps({
  selectedDate: { type: Date,   default: () => new Date() },
  dayRecord:    { type: Object, default: null }
});
const emit = defineEmits(['saved', 'deleted']); 

const loading = ref(false);
const form = reactive({
  readingStart: '', readingEnd: '',
  mathTitle: '', mathMin: '', mathSec: '',
  classTitle: '', classType: ''
});

// ── 今天 / 昨天/ 明天 才可编辑 ───────────────────────────────────
const isEditable = computed(() => {
  if (!props.selectedDate) return false;
  const sel       = new Date(props.selectedDate); sel.setHours(0,0,0,0);
  const today     = new Date(); today.setHours(0,0,0,0);
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
  const tomorrow  = new Date(today); tomorrow.setDate(today.getDate() + 1);
  return sel.getTime() === today.getTime()
      || sel.getTime() === yesterday.getTime()
      || sel.getTime() === tomorrow.getTime();
});

const formattedDate = computed(() => {
  const d = props.selectedDate;
  return `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日`;
});

// ── dayRecord 变化时填充表单 ──────────────────────────────
const populate = (record) => {
  form.readingStart = String(record?.reading_start ?? '');
  form.readingEnd   = String(record?.reading_end   ?? '');
  form.mathTitle    = record?.math_title  ?? '';
  form.mathMin      = String(record?.math_min ?? '');
  form.mathSec      = String(record?.math_sec ?? '');
  form.classTitle   = record?.class_title ?? '';
  form.classType    = record?.class_type  ?? '';
};

watch(
  [() => props.selectedDate, () => props.dayRecord],
  ([newDate, record]) => {
    // console.log("--- 选中日期已变化 ---", newDate);
    // console.log("--- 接收到的当条记录 ---", record);
    populate(record);
  },
  { immediate: true }
);

// ── 工具 ─────────────────────────────────────────────────
const showError  = (msg) => uni.showToast({ title: msg, icon: 'none', duration: 2000 });
const formatDate = (date) => {
  const y = date.getFullYear();
  const m = String(date.getMonth()+1).padStart(2,'0');
  const d = String(date.getDate()).padStart(2,'0');
  return `${y}-${m}-${d}`;
};

const validate = () => {
  if (!form.readingStart || !form.readingEnd)       return showError('请填写英语阅读页码'), false;
  if (!/^\d+$/.test(form.readingStart) || !/^\d+$/.test(form.readingEnd))
                                                     return showError('页码必须是数字'), false;
  if (Number(form.readingEnd) <= Number(form.readingStart))
                                                     return showError('结束页码必须大于开始页码'), false;
  if (!form.mathTitle.trim())                        return showError('请填写数学练习题目'), false;
  if (form.mathMin === '' || form.mathSec === '')    return showError('请填写数学练习时长'), false;
  if (!/^\d+$/.test(form.mathMin) || !/^\d+$/.test(form.mathSec))
                                                     return showError('时长必须是数字'), false;
  if (Number(form.mathMin) > 60)                     return showError('分钟不能超过60'), false;
  if (Number(form.mathSec) > 60)                     return showError('秒数不能超过60'), false;
  if (!form.classTitle.trim())                       return showError('请填写网课课程标题'), false;
  if (!form.classType)                               return showError('请选择网课类型'), false;
  return true;
};

const onBlockedTap = () => {
  uni.showToast({ title: '未到日期录入', icon: 'none', duration: 2000 });
};

const saveData = () => {
  if (!validate()) return;
  loading.value = true;

  uni.request({
    url: `${Global.BASE_URL}/`,
    method: 'POST',
    data: {
      method: 'saveStudyRecord',
      date:         formatDate(props.selectedDate),
      readingStart: form.readingStart,
      readingEnd:   form.readingEnd,
      mathTitle:    form.mathTitle,
      mathMin:      form.mathMin,
      mathSec:      form.mathSec,
      classTitle:   form.classTitle,
      classType:    form.classType
    },
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    success: (res) => {
      if (res.data?.code === 0) {
        uni.showToast({ title: '保存成功', icon: 'success' });
        emit('saved', formatDate(props.selectedDate));
      } else {
        showError(res.data?.msg || '保存失败');
      }
    },
    fail: () => showError('无法连接到服务器'),
    complete: () => { loading.value = false; }
  });
};


// 增加以下状态和计算属性
const deleteLoading = ref(false);
const hasRecord = computed(() => !!props.dayRecord); // 判断当前选中日期是否已有记录

// --- 增加删除相关的函数 ---
const confirmDelete = () => {
  uni.showModal({
    title: '确认删除',
    content: '确定要删除这一天的学习记录吗？删除后不可恢复。',
    confirmColor: '#FF2D55',
    success: (res) => {
      if (res.confirm) {
        executeDelete();
      }
    }
  });
};

const executeDelete = () => {
  deleteLoading.value = true;
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: 'POST',
    data: {
      method: 'deleteStudyRecord',
      date: formatDate(props.selectedDate)
    },
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    success: (res) => {
      if (res.data?.code === 0) {
        uni.showToast({ title: '删除成功', icon: 'success' });
        // 清空本地表单
        populate(null);
        // 通知父组件刷新日历数据
        emit('deleted', formatDate(props.selectedDate));
      } else {
        showError(res.data?.msg || '删除失败');
      }
    },
    fail: () => showError('无法连接到服务器'),
    complete: () => { deleteLoading.value = false; }
  });
};
</script>

<style lang="scss" scoped>
.entry-container { padding: 30rpx 20rpx; }

.date-banner {
  display: flex; justify-content: space-between; align-items: center;
  background: #fff1f2; border-radius: 16rpx; padding: 20rpx 30rpx; margin-bottom: 30rpx;
  .date-label { font-size: 32rpx; font-weight: bold; color: #FF2D55; }
  .edit-hint  { font-size: 22rpx; color: #FF2D55; }
  &.readonly-banner {
    background: #f5f5f5;
    .date-label, .edit-hint { color: #999; }
  }
}
.card {
  background: #fff; border-radius: 20rpx; padding: 30rpx; margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.03);
  .card-title { font-size: 32rpx; font-weight: bold; margin-bottom: 30rpx; color: #333; }
}
.input-row { display: flex; align-items: center; gap: 20rpx; .split { color: #999; } }
.time-row {
  display: flex; align-items: center; gap: 10rpx; font-size: 28rpx; color: #333;
  .time-input { display: flex; align-items: center; width: 140rpx; gap: 10rpx; }
}
.radio-row { padding-top: 10rpx; }

.action-row {
  display: flex;
  align-items: center;
  margin-top: 40rpx;
}

.card {
  // 原有样式不变，加上 position: relative 让遮罩能定位
  position: relative;
  background: #fff; border-radius: 20rpx; padding: 30rpx; margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.03);
  .card-title { font-size: 32rpx; font-weight: bold; margin-bottom: 30rpx; color: #333; }
}

// 透明拦截层，覆盖整个 card，不影响视觉
.block-mask {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 10;
  background: transparent;
}
</style>