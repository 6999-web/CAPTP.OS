<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

import Login from './components/Login.vue'

const isLoggedIn = ref(false)
const currentTime = ref('')
const route = useRoute()
const router = useRouter()
let timer = null

const navItems = [
  { to: '/shooting', icon: '🎯', label: '射击评估' },
  { to: '/grappling', icon: '🥋', label: '格斗评分' },
  { to: '/tactical', icon: '🧠', label: '决策推演' },
  { to: '/settings', icon: '⚙️', label: '系统设置' }
]

const pageTitle = computed(() => {
  const current = navItems.find((item) => item.to === route.path)
  return current?.label || 'CAPTP-OS'
})

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', { hour12: false })
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})

const handleLoginSuccess = () => {
  isLoggedIn.value = true
  if (route.path === '/') {
    router.push('/shooting')
  }
}

const logout = () => {
  isLoggedIn.value = false
}
</script>

<template>
  <div class="main-app" :class="{ 'logged-in': isLoggedIn }">
    <Login v-if="!isLoggedIn" @login-success="handleLoginSuccess" />

    <template v-else>
      <header class="top-bar">
        <div class="system-title">
          <span class="status-dot"></span>
          <span class="title-text">CAPTP-OS 警务实战综合训练平台</span>
          <span class="version-tag">V3.2.0</span>
        </div>
        <div class="top-meta">
          <div class="time-box">{{ currentTime }}</div>
          <RouterLink to="/settings" class="settings-shortcut" title="系统设置">⚙ 设置</RouterLink>
          <div class="user-chip">
            <span class="rank">一级警监</span>
            <span class="name">管理员</span>
            <button class="logout-btn" @click="logout" title="注销系统">⎋</button>
          </div>
        </div>
      </header>

      <div class="layout-container">
        <aside class="sidebar glass">
          <div class="sidebar-header">
            <img src="/school_badge.jpg" class="side-badge" alt="校徽">
            <div class="side-title">教研中心</div>
          </div>
          <div class="nav-container">
            <RouterLink
              v-for="item in navItems"
              :key="item.to"
              :to="item.to"
              class="nav-item"
              :class="{ active: route.path === item.to }"
            >
              <span class="nav-ico">{{ item.icon }}</span>{{ item.label }}
            </RouterLink>
          </div>
          <div class="status-area">
            <div class="stat-line"><span>算力节点</span> <span class="val">ONLINE</span></div>
            <div class="stat-line"><span>加密链路</span> <span class="val">ACTIVE</span></div>
            <div class="stat-line"><span>部署位置</span> <span class="val">GX-CENTER</span></div>
            <div class="stat-line"><span>当前页面</span> <span class="val">{{ pageTitle }}</span></div>
          </div>
        </aside>

        <main class="content-viewport">
          <div class="content-frame glass">
            <RouterView />
          </div>
        </main>
      </div>
    </template>
  </div>
</template>

<style>
:root {
  --bg-deep: #060b13;
  --bg-card: rgba(13, 23, 38, 0.68);
  --bg-active: rgba(20, 33, 58, 0.84);
  --primary: #00e5ff;
  --secondary: #0066cc;
  --text-main: #ffffff;
  --text-dim: #a1b8d2;
  --border: rgba(0, 229, 255, 0.24);
}

body {
  margin: 0;
  padding: 0;
  background-color: var(--bg-deep);
  color: var(--text-main);
  font-family: 'Inter', 'PingFang SC', sans-serif;
  overflow: hidden;
}

.main-app {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at 92% 8%, rgba(0, 102, 204, 0.28), transparent 44%),
    radial-gradient(circle at 0% 100%, rgba(0, 229, 255, 0.18), transparent 38%),
    #060b13;
}

.glass {
  background: rgba(10, 17, 28, 0.72);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.top-bar {
  min-height: 64px;
  background: rgba(10, 17, 28, 0.9);
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 clamp(16px, 2vw, 40px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5);
  z-index: 100;
}

.system-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #00ff88;
  border-radius: 50%;
  box-shadow: 0 0 8px #00ff88;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 0.4; }
  50% { opacity: 1; }
  100% { opacity: 0.4; }
}

.title-text {
  font-weight: 800;
  letter-spacing: 1px;
  font-size: clamp(13px, 1vw, 16px);
  color: var(--primary);
}

.version-tag {
  background: var(--bg-active);
  font-size: 10px;
  padding: 2px 6px;
  border: 1px solid var(--border);
  color: var(--text-dim);
}

.top-meta {
  display: flex;
  gap: 14px;
  align-items: center;
}

.time-box {
  font-family: monospace;
  color: var(--text-dim);
  font-size: 14px;
}

.settings-shortcut {
  color: var(--primary);
  border: 1px solid var(--border);
  text-decoration: none;
  border-radius: 999px;
  padding: 7px 14px;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.settings-shortcut:hover {
  background: rgba(0, 229, 255, 0.12);
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(0, 0, 0, 0.3);
  padding: 5px 15px;
  border-radius: 20px;
  border: 1px solid #1a3a5f;
}

.rank {
  font-size: 12px;
  color: var(--text-dim);
}

.logout-btn {
  background: none;
  border: none;
  color: #ff4d4d;
  cursor: pointer;
  font-size: 16px;
  padding: 0;
  margin-left: 10px;
}

.layout-container {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.sidebar {
  width: clamp(220px, 16vw, 280px);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: clamp(16px, 1.8vw, 30px) clamp(14px, 1.2vw, 20px);
  display: flex;
  align-items: center;
  gap: 15px;
  border-bottom: 1px solid rgba(0, 229, 255, 0.08);
  margin-bottom: 14px;
}

.side-badge {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  border: 1px solid var(--primary);
  box-shadow: 0 0 10px rgba(0, 229, 255, 0.2);
}

.side-title {
  font-size: 14px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: 2px;
}

.nav-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 0 12px;
}

.nav-item {
  color: var(--text-dim);
  padding: 14px 18px;
  text-align: left;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.25s;
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
}

.nav-ico {
  font-size: 14px;
  opacity: 0.8;
}

.nav-item:hover {
  background: rgba(0, 229, 255, 0.06);
  color: var(--primary);
}

.nav-item.active {
  background: linear-gradient(90deg, rgba(0, 229, 255, 0.16) 0%, rgba(0, 229, 255, 0) 100%);
  color: var(--primary);
  border-left: 3px solid var(--primary);
}

.status-area {
  padding: 20px;
  border-top: 1px solid var(--border);
  background: rgba(0, 0, 0, 0.2);
}

.stat-line {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #3d5875;
  margin-bottom: 8px;
  font-family: monospace;
}

.stat-line .val {
  color: var(--primary);
}

.content-viewport {
  flex: 1;
  min-width: 0;
  min-height: 0;
  padding: clamp(12px, 1.4vw, 24px);
  display: flex;
}

.content-frame {
  width: 100%;
  height: 100%;
  min-height: 0;
  border: 1px solid rgba(0, 229, 255, 0.12);
  border-radius: 12px;
  padding: clamp(12px, 1.2vw, 22px);
  overflow: hidden;
}

.panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 24px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.38);
}

.panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, var(--primary), transparent);
}

h1 {
  font-size: clamp(20px, 1.8vw, 30px);
  font-weight: 900;
  letter-spacing: 1px;
  margin-top: 0;
  color: #fff;
  border-left: 5px solid var(--primary);
  padding-left: 14px;
  margin-bottom: 10px;
}

h2 {
  color: var(--primary);
  font-size: 18px;
  margin-top: 0;
  text-transform: uppercase;
  letter-spacing: 1px;
}

p {
  color: var(--text-dim);
  line-height: 1.6;
}

.btn {
  background: var(--secondary);
  color: white;
  border: 1px solid var(--primary);
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: bold;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.25s;
  box-shadow: 0 0 15px rgba(0, 102, 204, 0.4);
}

.btn:hover:not(:disabled) {
  background: var(--primary);
  color: var(--bg-deep);
  box-shadow: 0 0 25px rgba(0, 229, 255, 0.5);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  border-color: #3d5875;
}

@media (max-width: 980px) {
  .sidebar {
    width: 84px;
  }

  .side-title,
  .status-area,
  .nav-item {
    font-size: 0;
  }

  .nav-item {
    justify-content: center;
    padding: 12px;
  }

  .nav-ico {
    font-size: 18px;
    opacity: 1;
  }

  .top-meta {
    gap: 10px;
  }

  .rank,
  .name {
    display: none;
  }
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: #1a3a5f; }
::-webkit-scrollbar-thumb:hover { background: var(--primary); }
</style>
