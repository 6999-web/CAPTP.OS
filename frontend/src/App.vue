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

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', { hour12: false })
}

onMounted(() => {
  setInterval(updateTime, 1000)
})

const handleLoginSuccess = () => {
  isLoggedIn.value = true
}

const setView = (viewName) => {
  currentView.value = viewName
}

const logout = () => {
  isLoggedIn.value = false
}
</script>

<template>
  <div class="main-app" :class="{ 'logged-in': isLoggedIn }">
    <!-- 登录模块 -->
    <Login v-if="!isLoggedIn" @login-success="handleLoginSuccess" />

    <!-- 主体框架 -->
    <template v-else>
      <header class="top-bar">
        <div class="system-title">
          <span class="status-dot"></span>
          <span class="title-text">CAPTP-OS: 智警实战综合训练云终端</span>
          <span class="version-tag">V3.1.2-ALPHA</span>
        </div>
        <div class="top-meta">
          <div class="time-box">{{ currentTime }}</div>
          <div class="user-chip">
            <span class="rank">一级警督</span>
            <span class="name">管理员</span>
            <button class="logout-btn" @click="logout" title="注销系统">🚪</button>
          </div>
        </div>
      </header>

      <div class="layout-container">
        <aside class="sidebar">
          <div class="sidebar-header">
            <img src="/school_badge.jpg" class="side-badge" alt="校徽">
            <div class="side-title">教研中心</div>
          </div>
          <div class="nav-container">
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
          </div>
        </aside>

        <main class="content-viewport">
          <div class="content-frame">
              <Overview v-if="currentView === 'overview'" />
              <Shooting v-else-if="currentView === 'shooting'" />
              <Grappling v-else-if="currentView === 'grappling'" />
              <Tactical v-else-if="currentView === 'tactical'" />
          </div>
        </main>
      </div>
    </template>
  </div>
</template>

<style>
/* 全局高级感重置 */
:root {
  --bg-deep: #060b13;
  --bg-card: #0d1726;
  --bg-active: #14213a;
  --primary: #00e5ff;
  --secondary: #0066cc;
  --text-main: #ffffff;
  --text-dim: #a1b8d2;
  --border: rgba(0, 229, 255, 0.2);
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
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.top-bar {
  height: 60px;
  background: #0a111c;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.5);
  z-index: 100;
}

.system-title {
  display: flex;
  align-items: center;
  gap: 15px;
}

.status-dot {
  width: 8px; height: 8px;
  background: #00ff88;
  border-radius: 50%;
  box-shadow: 0 0 8px #00ff88;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; }
}

.title-text {
  font-weight: 800;
  letter-spacing: 2px;
  font-size: 16px;
  color: var(--primary);
  text-transform: uppercase;
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
  gap: 30px;
  align-items: center;
}

.time-box {
  font-family: monospace;
  color: var(--text-dim);
  font-size: 14px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(0,0,0,0.3);
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
  overflow: hidden;
}

.sidebar {
  width: 260px;
  background: #0a111c;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 30px 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  border-bottom: 1px solid rgba(0,229,255,0.05);
  margin-bottom: 20px;
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
  color: var(--primary);
  border-left: 3px solid var(--primary);
}

.status-area {
  padding: 30px;
  border-top: 1px solid var(--border);
  background: rgba(0,0,0,0.2);
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
}

.panel::before {
  content: '';
  position: absolute;
  top:0; left:0; width: 100%; height: 2px;
  background: linear-gradient(90deg, var(--primary), transparent);
}

h1 {
  font-size: 32px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-top: 0;
  color: #fff;
  border-left: 5px solid var(--primary);
  padding-left: 20px;
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
  padding: 12px 30px;
  border-radius: 4px;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 2px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 0 15px rgba(0, 102, 204, 0.4);
}

.btn:hover:not(:disabled) {
  background: var(--primary);
  color: var(--bg-deep);
  box-shadow: 0 0 25px rgba(0, 229, 255, 0.6);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  border-color: #3d5875;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: #1a3a5f; }
::-webkit-scrollbar-thumb:hover { background: var(--primary); }
</style>
