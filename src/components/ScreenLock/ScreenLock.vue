<template>
  <view class="screen-lock" v-if="showLock">
    <view class="lock-overlay">
      <view class="lock-card">
        <!-- App Logo & Title -->
        <image class="lock-logo" src="/static/dailycheckin.png" mode="aspectFit" />
        <text class="lock-title">DailyCheck Sophia</text>
        <text class="lock-subtitle">请输入密码解锁</text>

        <!-- Password Input Display -->
        <view class="password-dots">
          <view
            v-for="i in 6"
            :key="i"
            class="dot"
            :class="{ filled: i <= pwdInput.length }"
          />
        </view>

        <!-- Error Message -->
        <text v-if="errorMsg" class="error-msg">{{ errorMsg }}</text>

        <!-- Numeric Keypad -->
        <view class="keypad">
          <view class="keypad-row">
            <view
              v-for="n in [1, 2, 3]"
              :key="n"
              class="key"
              @tap="onKeyPress(n)"
            >
              <text class="key-text">{{ n }}</text>
            </view>
          </view>
          <view class="keypad-row">
            <view
              v-for="n in [4, 5, 6]"
              :key="n"
              class="key"
              @tap="onKeyPress(n)"
            >
              <text class="key-text">{{ n }}</text>
            </view>
          </view>
          <view class="keypad-row">
            <view
              v-for="n in [7, 8, 9]"
              :key="n"
              class="key"
              @tap="onKeyPress(n)"
            >
              <text class="key-text">{{ n }}</text>
            </view>
          </view>
          <view class="keypad-row">
            <view class="key empty" />
            <view class="key" @tap="onKeyPress(0)">
              <text class="key-text">0</text>
            </view>
            <view class="key" @tap="onDelete">
              <text class="key-text delete-icon">⌫</text>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const STORAGE_KEY = 'app_lock_data'
const CORRECT_PASSWORD = '258369'
const EXPIRY_DAYS = 7

const showLock = ref(true)
const pwdInput = ref('')
const errorMsg = ref('')
let autoChecked = false

// --- Encryption utils ---

async function hashPassword(password) {
  const encoder = new TextEncoder()
  const data = encoder.encode(password + '_app_salt_2026')
  try {
    const hashBuffer = await crypto.subtle.digest('SHA-256', data)
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
  } catch {
    // Fallback if SubtleCrypto not available
    let hash = 0
    for (let i = 0; i < data.length; i++) {
      hash = ((hash << 5) - hash) + data[i]
      hash |= 0
    }
    return 'h_' + Math.abs(hash).toString(36)
  }
}

function getStoredData() {
  try {
    const raw = uni.getStorageSync(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function isExpired(timestamp) {
  const now = Date.now()
  const diff = now - timestamp
  return diff > EXPIRY_DAYS * 24 * 60 * 60 * 1000
}

async function setStoredData() {
  const hash = await hashPassword(CORRECT_PASSWORD)
  const data = JSON.stringify({ hash, timestamp: Date.now() })
  uni.setStorageSync(STORAGE_KEY, data)
}

// --- Auto-check on mount ---

async function checkAuth() {
  const stored = getStoredData()
  if (!stored) {
    showLock.value = true
    return
  }
  if (isExpired(stored.timestamp)) {
    uni.removeStorageSync(STORAGE_KEY)
    showLock.value = true
    return
  }
  // Verify stored hash matches the correct password hash
  const expectedHash = await hashPassword(CORRECT_PASSWORD)
  if (stored.hash === expectedHash) {
    showLock.value = false
  } else {
    uni.removeStorageSync(STORAGE_KEY)
    showLock.value = true
  }
}

// --- User input handling ---

async function onKeyPress(num) {
  errorMsg.value = ''
  if (pwdInput.value.length >= 6) return
  pwdInput.value += String(num)

  if (pwdInput.value.length === 6) {
    await verifyPassword()
  }
}

function onDelete() {
  errorMsg.value = ''
  if (pwdInput.value.length > 0) {
    pwdInput.value = pwdInput.value.slice(0, -1)
  }
}

async function verifyPassword() {
  if (pwdInput.value === CORRECT_PASSWORD) {
    await setStoredData()
    showLock.value = false
  } else {
    errorMsg.value = '密码错误，请重试'
    pwdInput.value = ''
    // Slight delay so user can see the error
    setTimeout(() => {
      errorMsg.value = ''
    }, 2000)
  }
}

// --- Lifecycle ---

onMounted(async () => {
  if (autoChecked) return
  autoChecked = true
  await checkAuth()
})
</script>

<style lang="scss">
.screen-lock {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99999;
}

.lock-overlay {
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.lock-card {
  width: 320px;
  padding: 40px 30px 30px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.lock-logo {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  margin-bottom: 16px;
}

.lock-title {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 4px;
}

.lock-subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 24px;
}

.password-dots {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.4);
  transition: all 0.2s;
}

.dot.filled {
  background: #fff;
  border-color: #fff;
  box-shadow: 0 0 6px rgba(255, 255, 255, 0.5);
}

.error-msg {
  font-size: 13px;
  color: #ff6b6b;
  margin-bottom: 12px;
  animation: shake 0.3s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-6px); }
  75% { transform: translateX(6px); }
}

.keypad {
  width: 100%;
}

.keypad-row {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 12px;
}

.key {
  width: 72px;
  height: 56px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
  user-select: none;
  -webkit-user-select: none;
}

.key:active {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(0.92);
}

.key.empty {
  background: transparent;
  cursor: default;
}

.key.empty:active {
  background: transparent;
  transform: none;
}

.key-text {
  font-size: 24px;
  font-weight: 500;
  color: #fff;
}

.delete-icon {
  font-size: 22px;
  color: rgba(255, 255, 255, 0.7);
}
</style>
