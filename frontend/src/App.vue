<<<<<<< HEAD
﻿<script setup>
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
=======
<script setup>
import { ref, onMounted } from 'vue'
import Login from './components/Login.vue'
import Overview from './components/Overview.vue'
import Shooting from './components/Shooting.vue'
import Grappling from './components/Grappling.vue'
import Tactical from './components/Tactical.vue'

const isLoggedIn = ref(false)
const currentView = ref('overview')
const currentTime = ref('')
>>>>>>> origin/main

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', { hour12: false })
}

onMounted(() => {
<<<<<<< HEAD
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
=======
  setInterval(updateTime, 1000)
>>>>>>> origin/main
})

const handleLoginSuccess = () => {
  isLoggedIn.value = true
<<<<<<< HEAD
  if (route.path === '/') {
    router.push('/shooting')
  }
=======
}

const setView = (viewName) => {
  currentView.value = viewName
>>>>>>> origin/main
}

const logout = () => {
  isLoggedIn.value = false
}
</script>

<template>
  <div class="main-app" :class="{ 'logged-in': isLoggedIn }">
<<<<<<< HEAD
    <Login v-if="!isLoggedIn" @login-success="handleLoginSuccess" />

=======
    <!-- 登录模块 -->
    <Login v-if="!isLoggedIn" @login-success="handleLoginSuccess" />

    <!-- 主体框架 -->
>>>>>>> origin/main
    <template v-else>
      <header class="top-bar">
        <div class="system-title">
          <span class="status-dot"></span>
<<<<<<< HEAD
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
=======
          <span class="title-text">CAPTP-OS: 智警实战综合训练云终端</span>
          <span class="version-tag">V3.1.2-ALPHA</span>
        </div>
        <div class="top-meta">
          <div class="time-box">{{ currentTime }}</div>
          <div class="user-chip">
            <span class="rank">一级警督</span>
            <span class="name">管理员</span>
            <button class="logout-btn" @click="logout" title="注销系统">🚪</button>
>>>>>>> origin/main
          </div>
        </div>
      </header>

      <div class="layout-container">
<<<<<<< HEAD
        <aside class="sidebar glass">
=======
        <aside class="sidebar">
>>>>>>> origin/main
          <div class="sidebar-header">
            <img src="/school_badge.jpg" class="side-badge" alt="校徽">
            <div class="side-title">教研中心</div>
          </div>
          <div class="nav-container">
<<<<<<< HEAD
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
=======
            <button :class="{ active: currentView === 'overview' }" @click="setView('overview')">
              <span class="nav-ico">🏠</span> 终端概览
            </button>
            <button :class="{ active: currentView === 'shooting' }" @click="setView('shooting')">
              <span class="nav-ico">🎯</span> 射击评估
            </button>
            <button :class="{ active: currentView === 'grappling' }" @click="setView('grappling')">
              <span class="nav-ico">🥋</span> 格斗评分
            </button>
            <button :class="{ active: currentView === 'tactical' }" @click="setView('tactical')">
              <span class="nav-ico">🧠</span> 决策推演
            </button>
          </div>
          <div class="status-area">
             <div class="stat-line"><span>运算核心 (NVIDIA)</span> <span class="val">ONLINE</span></div>
             <div class="stat-line"><span>加密链路 (TLS)</span> <span class="val">ACTIVE</span></div>
             <div class="stat-line"><span>节点位置</span> <span class="val">GX-CENTER</span></div>
>>>>>>> origin/main
          </div>
        </aside>

        <main class="content-viewport">
<<<<<<< HEAD
          <div class="content-frame glass">
            <RouterView />
=======
          <div class="content-frame">
              <Overview v-if="currentView === 'overview'" />
              <Shooting v-else-if="currentView === 'shooting'" />
              <Grappling v-else-if="currentView === 'grappling'" />
              <Tactical v-else-if="currentView === 'tactical'" />
>>>>>>> origin/main
          </div>
        </main>
      </div>
    </template>
  </div>
</template>

<style>
<<<<<<< HEAD
:root {
  --bg-deep: #060b13;
  --bg-card: rgba(13, 23, 38, 0.68);
  --bg-active: rgba(20, 33, 58, 0.84);
=======
/* 全局高级感重置 */
:root {
  --bg-deep: #060b13;
  --bg-card: #0d1726;
  --bg-active: #14213a;
>>>>>>> origin/main
  --primary: #00e5ff;
  --secondary: #0066cc;
  --text-main: #ffffff;
  --text-dim: #a1b8d2;
<<<<<<< HEAD
  --border: rgba(0, 229, 255, 0.24);
=======
  --border: rgba(0, 229, 255, 0.2);
>>>>>>> origin/main
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
<<<<<<< HEAD
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
=======
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.top-bar {
  height: 60px;
  background: #0a111c;
>>>>>>> origin/main
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
<<<<<<< HEAD
  padding: 0 clamp(16px, 2vw, 40px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5);
=======
  padding: 0 40px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.5);
>>>>>>> origin/main
  z-index: 100;
}

.system-title {
  display: flex;
  align-items: center;
<<<<<<< HEAD
  gap: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
=======
  gap: 15px;
}

.status-dot {
  width: 8px; height: 8px;
>>>>>>> origin/main
  background: #00ff88;
  border-radius: 50%;
  box-shadow: 0 0 8px #00ff88;
  animation: pulse 2s infinite;
}

@keyframes pulse {
<<<<<<< HEAD
  0% { opacity: 0.4; }
  50% { opacity: 1; }
  100% { opacity: 0.4; }
=======
  0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; }
>>>>>>> origin/main
}

.title-text {
  font-weight: 800;
<<<<<<< HEAD
  letter-spacing: 1px;
  font-size: clamp(13px, 1vw, 16px);
  color: var(--primary);
=======
  letter-spacing: 2px;
  font-size: 16px;
  color: var(--primary);
  text-transform: uppercase;
>>>>>>> origin/main
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
<<<<<<< HEAD
  gap: 14px;
=======
  gap: 30px;
>>>>>>> origin/main
  align-items: center;
}

.time-box {
  font-family: monospace;
  color: var(--text-dim);
  font-size: 14px;
}

<<<<<<< HEAD
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

=======
>>>>>>> origin/main
.user-chip {
  display: flex;
  align-items: center;
  gap: 12px;
<<<<<<< HEAD
  background: rgba(0, 0, 0, 0.3);
=======
  background: rgba(0,0,0,0.3);
>>>>>>> origin/main
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
<<<<<<< HEAD
  min-height: 0;
=======
>>>>>>> origin/main
  overflow: hidden;
}

.sidebar {
<<<<<<< HEAD
  width: clamp(220px, 16vw, 280px);
=======
  width: 260px;
  background: #0a111c;
>>>>>>> origin/main
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
<<<<<<< HEAD
  padding: clamp(16px, 1.8vw, 30px) clamp(14px, 1.2vw, 20px);
  display: flex;
  align-items: center;
  gap: 15px;
  border-bottom: 1px solid rgba(0, 229, 255, 0.08);
  margin-bottom: 14px;
=======
  padding: 30px 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  border-bottom: 1px solid rgba(0,229,255,0.05);
  margin-bottom: 20px;
>>>>>>> origin/main
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
<<<<<<< HEAD
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
=======
  gap: 5px;
  padding: 0 20px;
}

.nav-container button {
  background: none;
  border: none;
  color: var(--text-dim);
  padding: 15px 25px;
  text-align: left;
  border-radius: 4px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 15px;
}

.nav-ico { font-size: 14px; opacity: 0.7; }

.nav-container button:hover {
  background: rgba(0, 229, 255, 0.05);
  color: var(--primary);
}

.nav-container button.active {
  background: linear-gradient(90deg, rgba(0, 229, 255, 0.15) 0%, rgba(0, 229, 255, 0) 100%);
>>>>>>> origin/main
  color: var(--primary);
  border-left: 3px solid var(--primary);
}

.status-area {
<<<<<<< HEAD
  padding: 20px;
  border-top: 1px solid var(--border);
  background: rgba(0, 0, 0, 0.2);
=======
  padding: 30px;
  border-top: 1px solid var(--border);
  background: rgba(0,0,0,0.2);
>>>>>>> origin/main
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
<<<<<<< HEAD
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
=======
  padding: 40px;
  background: radial-gradient(circle at top right, #0d1726 0%, #060b13 70%);
  overflow-y: auto;
}

.content-frame {
  max-width: 1400px;
  margin: 0 auto;
}

/* 统一卡片样式 */
.panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 30px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0,0,0,0.4);
>>>>>>> origin/main
}

.panel::before {
  content: '';
  position: absolute;
<<<<<<< HEAD
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
=======
  top:0; left:0; width: 100%; height: 2px;
>>>>>>> origin/main
  background: linear-gradient(90deg, var(--primary), transparent);
}

h1 {
<<<<<<< HEAD
  font-size: clamp(20px, 1.8vw, 30px);
  font-weight: 900;
  letter-spacing: 1px;
  margin-top: 0;
  color: #fff;
  border-left: 5px solid var(--primary);
  padding-left: 14px;
=======
  font-size: 32px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-top: 0;
  color: #fff;
  border-left: 5px solid var(--primary);
  padding-left: 20px;
>>>>>>> origin/main
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
<<<<<<< HEAD
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: bold;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.25s;
=======
  padding: 12px 30px;
  border-radius: 4px;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 2px;
  cursor: pointer;
  transition: all 0.3s;
>>>>>>> origin/main
  box-shadow: 0 0 15px rgba(0, 102, 204, 0.4);
}

.btn:hover:not(:disabled) {
  background: var(--primary);
  color: var(--bg-deep);
<<<<<<< HEAD
  box-shadow: 0 0 25px rgba(0, 229, 255, 0.5);
=======
  box-shadow: 0 0 25px rgba(0, 229, 255, 0.6);
>>>>>>> origin/main
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  border-color: #3d5875;
}

<<<<<<< HEAD
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

=======
>>>>>>> origin/main
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: #1a3a5f; }
::-webkit-scrollbar-thumb:hover { background: var(--primary); }
</style>
