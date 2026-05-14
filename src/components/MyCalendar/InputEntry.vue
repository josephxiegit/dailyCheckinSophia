<template>
  <view class="entry-container">
    <view v-if="showCompleteFeedback" class="complete-feedback">
      <image
        class="complete-image"
        src="/static/review_complete.jpeg"
        mode="widthFix"
      />
    </view>

    <view class="date-banner" :class="{ 'readonly-banner': !isEditable }">
      <text class="date-label">{{ formattedDate }}</text>
      <text class="edit-hint">{{ isEditable ? '✏️ 可编辑' : '👁 仅查看（只支持今天和昨天）' }}</text>
    </view>

    <!-- 英语阅读 -->
    <view class="card" :class="{ 'card--locked': isLockedReading }">
      <view class="card-title"><text class="card-icon">📖</text> 英语阅读</view>
      <view class="input-row">
        <u-input v-model="form.readingStart" placeholder="开始页码" type="number"
          :disabled="!isEditable || isLockedReading" :border="false"
          customStyle="border-bottom: 1px solid #f0f0f0;"></u-input>
        <text class="split">-</text>
        <u-input v-model="form.readingEnd" placeholder="结束页码" type="number"
          :disabled="!isEditable || isLockedReading" :border="false"
          customStyle="border-bottom: 1px solid #f0f0f0;"></u-input>
      </view>
      <view v-if="isEditable" class="card-action-row">
        <u-button
          v-if="isLockedReading"
          text="编辑阅读"
          color="#bbbbbb"
          size="small"
          customStyle="border-radius: 40rpx; flex: 1;"
          @click="editingReading = true"
        ></u-button>
        <u-button
          v-else
          text="保存阅读"
          color="#FF2D55"
          size="small"
          :loading="loadingReading"
          customStyle="border-radius: 40rpx; flex: 1;"
          @click="saveReading"
        ></u-button>
      </view>
      <view v-if="!isEditable" class="block-mask" @click="onBlockedTap"></view>
    </view>

    <!-- 数学练习 -->
    <view class="card" :class="{ 'card--locked': isLockedMath }">
      <view class="card-title"><text class="card-icon">🔢</text> 数学练习</view>
      <u-input v-model="form.mathTitle" placeholder="练习题目内容"
        :disabled="!isEditable || isLockedMath" :border="false"
        customStyle="border-bottom: 1px solid #f0f0f0; margin-bottom: 30rpx;"></u-input>
      <view class="time-row">
        <text class="label">时长：</text>
        <view class="time-input">
          <u-input v-model="form.mathMin" type="number" placeholder="分"
            :disabled="!isEditable || isLockedMath" :border="false"
            customStyle="border-bottom: 1px solid #f0f0f0;"></u-input>
          <text>分</text>
        </view>
        <view class="time-input">
          <u-input v-model="form.mathSec" type="number" placeholder="秒"
            :disabled="!isEditable || isLockedMath" :border="false"
            customStyle="border-bottom: 1px solid #f0f0f0;"></u-input>
          <text>秒</text>
        </view>
      </view>
      <view v-if="isEditable" class="card-action-row">
        <u-button
          v-if="isLockedMath"
          text="编辑数学"
          color="#bbbbbb"
          size="small"
          customStyle="border-radius: 40rpx; flex: 1;"
          @click="editingMath = true"
        ></u-button>
        <u-button
          v-else
          text="保存数学"
          color="#FF9500"
          size="small"
          :loading="loadingMath"
          customStyle="border-radius: 40rpx; flex: 1;"
          @click="saveMath"
        ></u-button>
      </view>
      <view v-if="!isEditable" class="block-mask" @click="onBlockedTap"></view>
    </view>

    <!-- 英语网课 -->
    <view class="card" :class="{ 'card--locked': isLockedClass }">
      <view class="card-title"><text class="card-icon">💻</text> 英语网课</view>
      <u-input v-model="form.classTitle" placeholder="课程标题"
        :disabled="!isEditable || isLockedClass" :border="false"
        customStyle="border-bottom: 1px solid #f0f0f0; margin-bottom: 30rpx;"></u-input>
      <view class="radio-row">
        <u-radio-group v-model="form.classType" placement="row">
          <u-radio label="上"   name="上"   activeColor="#34C759" :disabled="!isEditable || isLockedClass" customStyle="margin-right: 40rpx;"></u-radio>
          <u-radio label="下"   name="下"   activeColor="#34C759" :disabled="!isEditable || isLockedClass" customStyle="margin-right: 40rpx;"></u-radio>
          <u-radio label="全部" name="全部" activeColor="#34C759" :disabled="!isEditable || isLockedClass"></u-radio>
        </u-radio-group>
      </view>
      <view v-if="isEditable" class="card-action-row">
        <u-button
          v-if="isLockedClass"
          text="编辑网课"
          color="#bbbbbb"
          size="small"
          customStyle="border-radius: 40rpx; flex: 1;"
          @click="editingClass = true"
        ></u-button>
        <u-button
          v-else
          text="保存网课"
          color="#34C759"
          size="small"
          :loading="loadingClass"
          customStyle="border-radius: 40rpx; flex: 1;"
          @click="saveClass"
        ></u-button>
      </view>
      <view v-if="!isEditable" class="block-mask" @click="onBlockedTap"></view>
    </view>

    <!-- 删除按钮（独立在底部） -->
    <view v-if="isEditable && hasRecord" class="delete-row">
      <u-button
        text="删除当天全部记录"
        type="error"
        plain
        :loading="deleteLoading"
        customStyle="border-radius: 50rpx; width: 100%;"
        @click="confirmDelete"
      ></u-button>
    </view>

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

const hasRecord = computed(() => !!props.dayRecord);

const hasReading = computed(() => !!(props.dayRecord?.reading_start));
const hasMath    = computed(() => !!(props.dayRecord?.math_title));
const hasClass   = computed(() => !!(props.dayRecord?.class_title));

const isLockedReading = computed(() => hasReading.value && !editingReading.value);
const isLockedMath    = computed(() => hasMath.value    && !editingMath.value);
const isLockedClass   = computed(() => hasClass.value   && !editingClass.value);

// 辅助函数：将数字时间值转为字符串，若值为0或'0'则返回空字符串
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
  // 处理分秒：0 或 '0' 都转为空字符串
  form.mathMin = formatTimeValue(record?.math_min);
  form.mathSec = formatTimeValue(record?.math_sec);
  form.classTitle   = record?.class_title ?? '';
  form.classType    = record?.class_type  ?? '';
  
  editingReading.value = false;
  editingMath.value    = false;
  editingClass.value   = false;
};

watch(
  [() => props.selectedDate, () => props.dayRecord],
  ([, record]) => { populate(record); },
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
  if (!form.readingStart || !form.readingEnd)
    return showError('请填写英语阅读页码'), false;
  if (!/^\d+$/.test(form.readingStart) || !/^\d+$/.test(form.readingEnd))
    return showError('页码必须是数字'), false;
  if (Number(form.readingEnd) <= Number(form.readingStart))
    return showError('结束页码必须大于开始页码'), false;
  return true;
};

const validateMath = () => {
  if (!form.mathTitle.trim())
    return showError('请填写数学练习题目'), false;
  if (form.mathMin === '' || form.mathSec === '')
    return showError('请填写数学练习时长'), false;
  if (!/^\d+$/.test(form.mathMin) || !/^\d+$/.test(form.mathSec))
    return showError('时长必须是数字'), false;
  const minutes = parseInt(form.mathMin, 10);
  const seconds = parseInt(form.mathSec, 10);
  if (minutes > 60) return showError('分钟不能超过60'), false;
  if (seconds > 60) return showError('秒数不能超过60'), false;
  // 新增：时长不能全为0
  if (minutes === 0 && seconds === 0)
    return showError('时长不能全为0'), false;
  return true;
};

const validateClass = () => {
  if (!form.classTitle.trim())
    return showError('请填写网课课程标题'), false;
  if (!form.classType)
    return showError('请选择网课类型（上/下/全部）'), false;
  return true;
};

const saveReading = () => {
  if (!validateReading()) return;
  loadingReading.value = true;
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: 'POST',
    data: {
      method: 'saveStudyRecord',
      section: 'reading',
      date:         formatDate(props.selectedDate),
      readingStart: form.readingStart,
      readingEnd:   form.readingEnd,
    },
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    success: (res) => {
      if (res.data?.code === 0) {
        showSaveComplete();
        editingReading.value = false;
        emit('saved', formatDate(props.selectedDate));
      } else {
        showError(res.data?.msg || '保存失败');
      }
    },
    fail: () => showError('无法连接到服务器'),
    complete: () => { loadingReading.value = false; }
  });
};

const saveMath = () => {
  if (!validateMath()) return;
  loadingMath.value = true;
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: 'POST',
    data: {
      method: 'saveStudyRecord',
      section:   'math',
      date:      formatDate(props.selectedDate),
      mathTitle: form.mathTitle,
      mathMin:   form.mathMin,
      mathSec:   form.mathSec,
    },
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    success: (res) => {
      if (res.data?.code === 0) {
        showSaveComplete();
        editingMath.value = false;
        emit('saved', formatDate(props.selectedDate));
      } else {
        showError(res.data?.msg || '保存失败');
      }
    },
    fail: () => showError('无法连接到服务器'),
    complete: () => { loadingMath.value = false; }
  });
};

const saveClass = () => {
  if (!validateClass()) return;
  loadingClass.value = true;
  uni.request({
    url: `${Global.BASE_URL}/`,
    method: 'POST',
    data: {
      method:     'saveStudyRecord',
      section:    'class',
      date:       formatDate(props.selectedDate),
      classTitle: form.classTitle,
      classType:  form.classType,
    },
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    success: (res) => {
      if (res.data?.code === 0) {
        showSaveComplete();
        editingClass.value = false;
        emit('saved', formatDate(props.selectedDate));
      } else {
        showError(res.data?.msg || '保存失败');
      }
    },
    fail: () => showError('无法连接到服务器'),
    complete: () => { loadingClass.value = false; }
  });
};

const confirmDelete = () => {
  uni.showModal({
    title: '确认删除',
    content: '确定要删除这一天的全部学习记录吗？删除后不可恢复。',
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
        uni.showToast({ title: '删除成功', icon: 'success' });
        populate(null);
        emit('deleted', formatDate(props.selectedDate));
      } else {
        showError(res.data?.msg || '删除失败');
      }
    },
    fail: () => showError('无法连接到服务器'),
    complete: () => { deleteLoading.value = false; }
  });
};

onUnmounted(() => {
  if (completeFeedbackTimer) clearTimeout(completeFeedbackTimer);
  stopCompleteAudio();
  if (completeAudio) {
    completeAudio.destroy();
    completeAudio = null;
  }
});
</script>

<style lang="scss" scoped>
.entry-container { padding: 30rpx 20rpx; }

.complete-feedback {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.complete-image {
  width: 420rpx;
  max-width: 78vw;
  border-radius: 18rpx;
  box-shadow: 0 18rpx 50rpx rgba(0, 0, 0, 0.18);
}

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
  position: relative;
  background: #fff;
  border-radius: 20rpx; padding: 30rpx; margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.03);
  transition: background 0.2s;

  .card-title {
    font-size: 32rpx; font-weight: bold; margin-bottom: 30rpx;
    color: #333;
    transition: color 0.2s;
    
    .card-icon {
      margin-right: 8rpx;
      transition: all 0.2s;
    }
  }

  &.card--locked {
    background: #f7f7f7;
    box-shadow: none;
    
    .card-title { 
      color: #bbb; 
      .card-icon {
        filter: grayscale(100%);
        opacity: 0.6;
      }
    }
    
    text, .split, .label { color: #bbb !important; }
    
    :deep(input), :deep(.u-input__content__field-wrapper__field) {
      color: #bbb !important;
      -webkit-text-fill-color: #bbb !important;
    }
    
    :deep(.u-radio__text) {
      color: #bbb !important;
    }
  }
}

.card-action-row {
  display: flex;
  margin-top: 30rpx;
}

.input-row {
  display: flex; align-items: center; gap: 20rpx;
  .split { color: #999; }
}

.time-row {
  display: flex; align-items: center; gap: 10rpx; font-size: 28rpx; color: #333;
  .time-input { display: flex; align-items: center; width: 140rpx; gap: 10rpx; }
}

.radio-row { padding-top: 10rpx; }

.delete-row {
  margin-top: 10rpx;
  margin-bottom: 40rpx;
}

.block-mask {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 10;
  background: transparent;
}

@media (min-width: 1024px) {
  .entry-container {
    :deep(input),
    :deep(.u-input__content__field-wrapper__field),
    :deep(.u-radio__text),
    .label,
    .time-input text,
    .split {
      font-size: 16px !important;
    }
  }

  .complete-image {
    width: min(32vw, 520px);
    max-width: 520px;
  }
}
</style>
