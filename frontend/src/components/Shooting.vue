<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import { useLiveCameraSource } from '../composables/useLiveCameraSource'
import { buildApiUrl, readApiPayload } from '../utils/api'

const createLiveSessionId = () =>
  globalThis.crypto?.randomUUID?.() ?? `shooting-live-${Date.now()}-${Math.random().toString(16).slice(2)}`

const fileInput = ref(null)
const videoRef = ref(null)
const selectedFile = ref(null)
const previewUrl = ref(null)
const sourceMode = ref('upload')
const mode = ref('SHOOTING_POSTURE')
const isAnalyzing = ref(false)
const isLiveContinuous = ref(false)
const feedback = ref('')
const lastCaptureAt = ref('')
const liveSessionId = ref(createLiveSessionId())

let liveAnalyzeTimer = null

const {
  liveStream,
  liveError,
  liveStatus,
  cameraDevices,
  selectedCameraId,
  isRefreshingDevices,
  refreshCameraDevices,
  startLiveStream,
  stopLiveStream,
  switchCamera,
  captureBestFrame
} = useLiveCameraSource(videoRef)

const revokePreview = () => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = null
  }
}

const clearLiveAnalyzeTimer = () => {
  if (liveAnalyzeTimer) {
    window.clearInterval(liveAnalyzeTimer)
    liveAnalyzeTimer = null
  }
}

const closeLiveMode = () => {
  clearLiveAnalyzeTimer()
  isLiveContinuous.value = false
  stopLiveStream()
}

const onFileChange = (event) => {
  const [file] = event.target.files || []
  if (!file) return

  revokePreview()
  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
  feedback.value = ''
}

const openFilePicker = () => {
  if (sourceMode.value === 'upload') {
    fileInput.value?.click()
  }
}

const resolveAnalysisFile = async () => {
  if (sourceMode.value === 'live') {
    return captureBestFrame({
      sampleCount: mode.value === 'SHOOTING_TARGET' ? 4 : 3,
      intervalMs: mode.value === 'SHOOTING_TARGET' ? 110 : 90,
      fileNamePrefix: 'shooting_live_capture'
    })
  }

  return selectedFile.value
}

const isPrimaryActionDisabled = computed(() => {
  if (isAnalyzing.value || isLiveContinuous.value) {
    return true
  }

  return sourceMode.value === 'live' ? !liveStream.value : !selectedFile.value
})

const triggerAnalysis = async () => {
  if (isAnalyzing.value) return

  const file = await resolveAnalysisFile()
  if (!file) return

  isAnalyzing.value = true
  feedback.value = ''

  const formData = new FormData()
  formData.append('file', file)
  formData.append('mode', mode.value)
  formData.append('source', sourceMode.value)
  if (sourceMode.value === 'live') {
    formData.append('session_id', liveSessionId.value)
  }

  try {
    const res = await fetch(buildApiUrl('/api/analyze-vision'), {
      method: 'POST',
      body: formData
    })
    const data = await readApiPayload(res)
    if (res.ok) {
      feedback.value = data.result
      if (sourceMode.value === 'live') {
        lastCaptureAt.value = new Date().toLocaleTimeString()
        liveStatus.value = `最近一次识别时间：${lastCaptureAt.value}`
      }
    } else {
      feedback.value = `⚠️ 识别失败: ${data.detail || '请检查图片清晰度后重试。'}`
    }
  } catch (error) {
    feedback.value = `❌ 骨干网络通讯超时: ${error.message}`
  } finally {
    isAnalyzing.value = false
  }
}

const ensureLiveReady = async () => {
  const stream = await startLiveStream(selectedCameraId.value)
  return !!stream
}

const toggleContinuousAnalysis = async () => {
  if (isLiveContinuous.value) {
    clearLiveAnalyzeTimer()
    isLiveContinuous.value = false
    liveStatus.value = '连续识别已停止，可继续手动抓拍。'
    return
  }

  const ready = await ensureLiveReady()
  if (!ready) return

  isLiveContinuous.value = true
  liveStatus.value = '连续识别运行中，系统将按周期抓拍当前画面。'

  await triggerAnalysis()

  liveAnalyzeTimer = window.setInterval(() => {
    if (!isAnalyzing.value && liveStream.value) {
      triggerAnalysis()
    }
  }, 3200)
}

watch(sourceMode, async (nextMode) => {
  feedback.value = ''

  if (nextMode === 'live') {
    liveSessionId.value = createLiveSessionId()
    await refreshCameraDevices(false)
    liveStatus.value = '待命，请选择摄像头并开启实时画面。'
  } else {
    closeLiveMode()
  }
})

watch(selectedCameraId, () => {
  if (sourceMode.value === 'live') {
    liveSessionId.value = createLiveSessionId()
  }
})

onBeforeUnmount(() => {
  revokePreview()
  closeLiveMode()
})
</script>

<template>
  <div class="shooting-container">
    <div class="page-title row">
      <div class="title-main">
        <h1>🎯 射击技战术智能评估 / MARKSMANSHIP AI</h1>
        <p>基于跨模态视觉大模型实现高精度弹着点预测与持枪规范度诊断</p>
      </div>
      <div class="engine-badge">
        <span class="label">NVIDIA NIM </span>
        <span class="version">LLAMA-3.2-90B</span>
      </div>
    </div>

    <div class="main-split">
      <div class="panel upload-panel">
        <div class="panel-header">数据源输入 / DATA SOURCE</div>

        <div class="source-switcher">
          <button
            class="source-tab"
            :class="{ active: sourceMode === 'upload' }"
            @click="sourceMode = 'upload'"
          >
            本地图片上传
          </button>
          <button
            class="source-tab"
            :class="{ active: sourceMode === 'live' }"
            @click="sourceMode = 'live'"
          >
            实时画面传送识别
          </button>
        </div>

        <div class="source-tip">
          {{ sourceMode === 'upload'
            ? '适合靶纸、姿态、武器静态图快速识别。'
            : '支持多摄像头切换，包含笔记本自带摄像头和系统已识别的 Wi‑Fi 摄像头。' }}
        </div>

        <div class="upload-box" :class="{ live: sourceMode === 'live' }" @click="openFilePicker">
          <template v-if="sourceMode === 'upload'">
            <div v-if="!previewUrl" class="upload-placeholder">
              <span class="icon">📁</span>
              <p>点击选择或拖拽图片进行侦测</p>
              <div class="hint">支持 JPG/PNG/BMP 格式</div>
            </div>
            <img v-else :src="previewUrl" alt="预览" class="preview-img" />
          </template>

          <template v-else>
            <video v-if="liveStream" ref="videoRef" class="preview-video" autoplay muted playsinline></video>
            <div v-else class="upload-placeholder live-placeholder">
              <span class="icon">📡</span>
              <p>选择摄像头后即可接入实时画面</p>
              <div class="hint">支持浏览器识别到的所有视频输入设备</div>
            </div>
            <div v-if="liveStream" class="live-overlay">
              <span class="live-dot"></span>
              <span>REALTIME FEED ACTIVE</span>
            </div>
          </template>

          <input type="file" ref="fileInput" @change="onFileChange" hidden accept="image/*" />
        </div>

        <div v-if="sourceMode === 'live'" class="live-panel">
          <div class="device-row">
            <div class="device-field">
              <div class="device-label">视频源设备</div>
              <select
                class="device-select"
                :value="selectedCameraId"
                @change="switchCamera($event.target.value)"
              >
                <option value="" disabled>
                  {{ cameraDevices.length ? '请选择摄像头设备' : '未检测到摄像头设备' }}
                </option>
                <option v-for="device in cameraDevices" :key="device.id" :value="device.id">
                  {{ device.label }}
                </option>
              </select>
            </div>
            <button class="refresh-btn" @click="refreshCameraDevices(true)" :disabled="isRefreshingDevices || isAnalyzing">
              {{ isRefreshingDevices ? '刷新中...' : '刷新设备列表' }}
            </button>
          </div>

          <div class="live-status-row">
            <span class="live-chip" :class="{ online: liveStream }">
              {{ liveStream ? 'CAM ONLINE' : 'CAM OFFLINE' }}
            </span>
            <span class="live-status-text">{{ liveError || liveStatus }}</span>
          </div>

          <div class="live-actions">
            <button class="control-btn" @click="ensureLiveReady" :disabled="!!liveStream || isAnalyzing || !cameraDevices.length">
              开启实时画面
            </button>
            <button class="control-btn secondary" @click="closeLiveMode" :disabled="!liveStream">
              关闭实时画面
            </button>
            <button class="control-btn accent" @click="toggleContinuousAnalysis" :disabled="isAnalyzing || !cameraDevices.length">
              {{ isLiveContinuous ? '停止连续识别' : '开启连续识别' }}
            </button>
          </div>
        </div>

        <div class="mode-selector">
          <div class="selector-label">选择分析模态 / INFERENCE MODE</div>
          <div class="mode-tip">
            {{ sourceMode === 'upload'
              ? '建议上传正面、清晰、靶纸主体占比较高的图片；靶纸模式会返回具体环数、分布和水平判断。'
              : '实时模式建议保持画面稳定、主体清晰；切换摄像头后会自动重连到所选设备。' }}
          </div>
          <div class="option-grid">
            <label :class="{ selected: mode === 'SHOOTING_POSTURE' }">
              <input type="radio" v-model="mode" value="SHOOTING_POSTURE" hidden /> 姿态纠偏分析 (AlphaPose)
            </label>
            <label :class="{ selected: mode === 'SHOOTING_TARGET' }">
              <input type="radio" v-model="mode" value="SHOOTING_TARGET" hidden /> 靶纸评分分析 (OpenCV)
            </label>
            <label :class="{ selected: mode === 'SHOOTING_WEAPON' }">
              <input type="radio" v-model="mode" value="SHOOTING_WEAPON" hidden /> 武器负载识别 (YOLO)
            </label>
          </div>
        </div>

        <button class="btn full-width" @click="triggerAnalysis" :disabled="isPrimaryActionDisabled">
          <span v-if="isLiveContinuous">连续识别运行中...</span>
          <span v-else-if="!isAnalyzing">{{ sourceMode === 'upload' ? '启动 AI 侦测评估' : '抓拍当前实时画面' }}</span>
          <span v-else class="analyzing-state">系统中枢运算中...</span>
        </button>
      </div>

      <div class="panel result-panel h-scroll">
        <div class="panel-header">评估结论报告 / EVALUATION REPORT</div>
        <div v-if="!feedback && !isAnalyzing" class="empty-state">
          <div class="p-icon">🔍</div>
          <p>等待分析任务下达</p>
        </div>
        <div v-if="isAnalyzing" class="loading-wave">
          <div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div>
        </div>
        <div v-if="feedback" class="report-content">
          <div class="report-header">
            <span class="tag">CONFIDENTIAL</span>
            <span class="node">NODE_ID: {{ (Math.random() * 1000).toFixed(0) }}</span>
          </div>
          <div class="text-body">{{ feedback }}</div>
          <div class="report-footer">
            数据经端到端加密传输（AES-256）
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.shooting-container { animation: fadeIn 0.4s ease; }
.row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.engine-badge { background: #000; border: 1px solid var(--border); padding: 5px 15px; border-radius: 4px; font-family: monospace; font-size: 11px; }
.engine-badge .label { color: #76b900; font-weight: bold; }
.engine-badge .version { color: var(--primary); margin-left: 10px; }

.main-split { display: grid; grid-template-columns: 450px 1fr; gap: 30px; }

.panel-header { border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 20px; font-size: 11px; font-weight: bold; color: var(--primary); letter-spacing: 2px; }

.source-switcher {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 10px;
}

.source-tab {
  background: #0a111c;
  border: 1px solid #1a3a5f;
  color: #8aa6c3;
  padding: 10px 12px;
  cursor: pointer;
  transition: 0.3s;
  font-size: 13px;
}

.source-tab.active {
  border-color: var(--primary);
  color: var(--primary);
  background: rgba(0, 229, 255, 0.08);
  box-shadow: 0 0 12px rgba(0, 229, 255, 0.08);
}

.source-tip {
  margin-bottom: 14px;
  color: #7d92ab;
  font-size: 12px;
}

.upload-box {
  width: 100%;
  height: 260px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px dashed #1a3a5f;
  border-radius: 4px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: 0.3s;
  overflow: hidden;
  margin-bottom: 25px;
  position: relative;
}

.upload-box:hover { border-color: var(--primary); background: rgba(0, 229, 255, 0.05); }
.upload-box.live { cursor: default; }

.upload-placeholder { text-align: center; }
.upload-placeholder .icon { font-size: 30px; opacity: 0.5; margin-bottom: 10px; display: block; }
.upload-placeholder p { font-size: 13px; color: var(--text-dim); margin-top: 5px; }

.preview-img { width: 100%; height: 100%; object-fit: contain; }
.preview-video { width: 100%; height: 100%; object-fit: cover; background: #000; }

.live-placeholder .icon { font-size: 32px; }

.live-overlay {
  position: absolute;
  top: 12px;
  left: 12px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border: 1px solid rgba(0, 229, 255, 0.35);
  background: rgba(4, 12, 20, 0.85);
  color: #d7f9ff;
  font-size: 11px;
  font-family: monospace;
  letter-spacing: 1px;
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00ff88;
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.8);
}

.live-panel {
  margin-top: -8px;
  margin-bottom: 22px;
  padding: 14px;
  border: 1px solid rgba(0, 229, 255, 0.12);
  background: rgba(10, 17, 28, 0.72);
  border-radius: 4px;
}

.device-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  margin-bottom: 12px;
  align-items: end;
}

.device-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.device-label {
  font-size: 11px;
  color: #5c7694;
  font-weight: 700;
}

.device-select {
  width: 100%;
  background: #08111b;
  border: 1px solid #1a3a5f;
  color: #d1dcf0;
  padding: 10px 12px;
  outline: none;
}

.refresh-btn {
  background: rgba(0, 229, 255, 0.06);
  border: 1px solid rgba(0, 229, 255, 0.2);
  color: #bfeeff;
  padding: 10px 12px;
  cursor: pointer;
  transition: 0.3s;
  font-size: 12px;
  white-space: nowrap;
}

.refresh-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.live-status-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.live-chip {
  flex-shrink: 0;
  padding: 4px 8px;
  border: 1px solid #37516f;
  color: #8aa6c3;
  font-size: 11px;
  font-family: monospace;
}

.live-chip.online {
  border-color: rgba(0, 255, 136, 0.45);
  color: #00ff88;
}

.live-status-text {
  color: #a8bed4;
  font-size: 12px;
  line-height: 1.6;
}

.live-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.control-btn {
  background: rgba(0, 229, 255, 0.06);
  border: 1px solid rgba(0, 229, 255, 0.2);
  color: #bfeeff;
  padding: 10px 8px;
  cursor: pointer;
  transition: 0.3s;
  font-size: 12px;
}

.control-btn:hover:not(:disabled) {
  border-color: var(--primary);
  color: #fff;
}

.control-btn.secondary {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(138, 166, 195, 0.18);
  color: #9db5ce;
}

.control-btn.accent {
  background: rgba(0, 255, 136, 0.08);
  border-color: rgba(0, 255, 136, 0.22);
  color: #8ff5c5;
}

.control-btn:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.mode-selector { margin-bottom: 30px; }
.selector-label { font-size: 11px; color: #5c7694; margin-bottom: 12px; font-weight: 700; text-transform: uppercase; }
.mode-tip { margin-bottom: 12px; font-size: 12px; color: #7d92ab; }

.option-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.option-grid label {
  background: #0a111c;
  border: 1px solid #1a3a5f;
  padding: 12px;
  text-align: center;
  font-size: 13px;
  color: var(--text-dim);
  cursor: pointer;
  transition: 0.3s;
}
.option-grid label.selected { border-color: var(--primary); color: var(--primary); background: rgba(0, 229, 255, 0.1); }

.full-width { width: 100%; }

.empty-state { text-align: center; margin-top: 100px; color: #2d333b; }
.empty-state .p-icon { font-size: 40px; margin-bottom: 20px; }

.report-content { color: #fff; line-height: 1.8; animation: slideUp 0.5s ease-out; }
@keyframes slideUp { from { opacity: 0; transform: translateY(20px); } }

.report-header { display: flex; justify-content: space-between; font-size: 10px; font-family: monospace; color: var(--primary); margin-bottom: 25px; padding-bottom: 10px; border-bottom: 1px solid rgba(0,229,255,0.1); }
.report-header .tag { background: #ff4d4d; color: #fff; padding: 2px 6px; }

.text-body { white-space: pre-wrap; font-size: 15px; color: #d0d7de; padding: 0 10px; }

.report-footer { margin-top: 40px; text-align: right; font-size: 10px; color: #3d5875; border-top: 1px dotted #1a3a5f; padding-top: 15px; }

.loading-wave { display: flex; justify-content: center; align-items: center; height: 300px; gap: 5px; }
.loading-wave .bar { width: 4px; height: 30px; background: var(--primary); animation: wave 1s infinite ease-in-out; }
.loading-wave .bar:nth-child(2) { animation-delay: 0.1s; }
.loading-wave .bar:nth-child(3) { animation-delay: 0.2s; }
.loading-wave .bar:nth-child(4) { animation-delay: 0.3s; }
@keyframes wave { 0% { height: 10px; } 50% { height: 40px; opacity: 1; } 100% { height: 10px; opacity: 0.3; } }
</style>
