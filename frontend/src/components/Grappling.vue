<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import { useLiveCameraSource } from '../composables/useLiveCameraSource'
import { buildApiUrl, readApiPayload } from '../utils/api'

const createLiveSessionId = () =>
  globalThis.crypto?.randomUUID?.() ?? `grappling-live-${Date.now()}-${Math.random().toString(16).slice(2)}`

const fileInput = ref(null)
const videoRef = ref(null)
const selectedFile = ref(null)
const previewUrl = ref(null)
const isVideo = ref(false)
const sourceMode = ref('upload')
const mode = ref('COMBAT_FIGHT')
const isAnalyzing = ref(false)
const isLiveContinuous = ref(false)
const feedback = ref('')
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
  captureBurstContactSheet
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
  isVideo.value = file.type.startsWith('video/')
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
    return captureBurstContactSheet({
      frameCount: mode.value === 'COMBAT_SCORING' ? 4 : 3,
      intervalMs: mode.value === 'COMBAT_SCORING' ? 180 : 150,
      fileNamePrefix: 'grappling_live_capture'
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
        liveStatus.value = `最近一次识别时间：${new Date().toLocaleTimeString()}`
      }
    } else {
      feedback.value = `❌ 识别失败: ${data.detail || '请更换更清晰的训练画面后重试。'}`
    }
  } catch (error) {
    feedback.value = `❌ 通讯超时：${error.message}`
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
  }, 3500)
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
  <div class="grappling-container">
    <div class="header-row">
      <h1>🥋 擒拿格斗技战术评分 / COMBAT AI</h1>
      <div class="status-indicator">
        <span class="label">SKELETON_ENGINE</span>
        <span class="val">ACTIVE_99.1%</span>
      </div>
    </div>

    <div class="grid-layout">
      <div class="panel left-capture">
        <div class="panel-header">实战画面截帧 / COMBAT FRAME CAPTURE</div>

        <div class="source-switcher">
          <button class="source-tab" :class="{ active: sourceMode === 'upload' }" @click="sourceMode = 'upload'">
            本地图片/视频
          </button>
          <button class="source-tab" :class="{ active: sourceMode === 'live' }" @click="sourceMode = 'live'">
            实时画面传送识别
          </button>
        </div>

        <div class="source-tip">
          {{ sourceMode === 'upload'
            ? '支持训练图片和视频上传；视频会自动抽取关键帧做综合识别。'
            : '支持选择笔记本摄像头或系统已识别的 Wi‑Fi 摄像头进行实时抓拍识别。' }}
        </div>

        <div class="upload-area" :class="{ live: sourceMode === 'live' }" @click="openFilePicker">
          <template v-if="sourceMode === 'upload'">
            <div v-if="!previewUrl" class="placeholder">
              <div class="badge">SENSING</div>
              <p>放入训练图片或视频进行多维动作分析</p>
            </div>
            <img v-else-if="!isVideo" :src="previewUrl" class="preview-img" />
            <video v-else :src="previewUrl" class="preview-video" autoplay loop muted playsinline></video>
          </template>

          <template v-else>
            <video v-if="liveStream" ref="videoRef" class="preview-video live-stream" autoplay muted playsinline></video>
            <div v-else class="placeholder live-placeholder">
              <div class="badge">LIVE</div>
              <p>选择摄像头后开启实时画面</p>
            </div>
            <div v-if="liveStream" class="live-overlay">
              <span class="live-dot"></span>
              <span>REALTIME FEED ACTIVE</span>
            </div>
          </template>

          <input type="file" ref="fileInput" @change="onFileChange" hidden accept="image/*,video/*" />
        </div>

        <div v-if="sourceMode === 'live'" class="live-panel">
          <div class="device-row">
            <div class="device-field">
              <div class="device-label">视频源设备</div>
              <select class="device-select" :value="selectedCameraId" @change="switchCamera($event.target.value)">
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

        <div class="mode-selector-panel">
          <div class="label">分析模式选择 / SELECT MODE</div>
          <div class="btn-group">
            <button :class="{ active: mode === 'COMBAT_FIGHT' }" @click="mode = 'COMBAT_FIGHT'">暴力识别 (FightDetect)</button>
            <button :class="{ active: mode === 'COMBAT_SCORING' }" @click="mode = 'COMBAT_SCORING'">对抗评分 (UFC Logic)</button>
          </div>
          <div class="mode-tip">
            {{ sourceMode === 'upload'
              ? '上传视频时，系统会自动抽取多帧综合识别；评分结果会重点输出双方动作和可能伤害。'
              : '实时模式支持摄像头切换；切换设备后会自动重连到新的实时视频源。' }}
          </div>
        </div>

        <div class="controls">
          <button class="btn accent-btn" @click="triggerAnalysis" :disabled="isPrimaryActionDisabled">
            <span v-if="isLiveContinuous">连续识别运行中...</span>
            <span v-else-if="!isAnalyzing">{{ sourceMode === 'upload' ? '执行多维评估指令' : '抓拍当前实时画面' }}</span>
            <span v-else>正在进行神经元推理...</span>
          </button>
        </div>
      </div>

      <div class="panel right-analytics scrollable">
        <div class="panel-header">技战术解构报告 / TACTICAL DECONSTRUCTION</div>
        <div v-if="isAnalyzing" class="dna-spinner">
          <div class="dot"></div><div class="dot"></div><div class="dot"></div>
        </div>
        <div v-if="feedback" class="report-box">
          <div class="report-info"><span class="chip">ENCRYPTED</span> 绝密：仅限培训评估使用</div>
          <div class="text-content">{{ feedback }}</div>
          <div class="report-footer">END_OF_TRANSMISSION</div>
        </div>
        <div v-if="!feedback && !isAnalyzing" class="empty-notif">
          等待输入信号源进行实时动作建模分析...
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grappling-container { animation: fadeIn 0.4s ease; }
.header-row { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 30px; }
.status-indicator { font-family: monospace; font-size: 10px; background: #000; border: 1px solid var(--border); padding: 5px 12px; }
.status-indicator .label { color: #5c7694; margin-right: 10px; }
.status-indicator .val { color: var(--primary); font-weight: bold; }

.grid-layout { display: grid; grid-template-columns: 480px 1fr; gap: 30px; align-items: start; }

.panel-header { border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 25px; font-size: 11px; text-transform: uppercase; color: var(--primary); letter-spacing: 2px; }

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
}

.source-tip {
  margin-bottom: 14px;
  color: #7d92ab;
  font-size: 12px;
}

.upload-area {
  width: 100%;
  aspect-ratio: 16/10;
  background: rgba(0,0,0,0.5);
  border: 1px solid #1a3a5f;
  margin-bottom: 20px;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.upload-area.live { cursor: default; }
.upload-area::after { content: ''; position: absolute; inset: 10px; border: 1px solid rgba(0,229,255,0.05); pointer-events: none; }

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
  font-weight: bold;
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

.live-panel {
  margin-bottom: 20px;
  padding: 14px;
  border: 1px solid rgba(0, 229, 255, 0.12);
  background: rgba(10, 17, 28, 0.72);
  border-radius: 4px;
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

.mode-selector-panel { margin-bottom: 25px; }
.mode-selector-panel .label { font-size: 11px; color: #5c7694; margin-bottom: 10px; font-weight: bold; }
.mode-tip { margin-top: 10px; font-size: 12px; color: #7d92ab; }
.btn-group { display: flex; gap: 10px; }
.btn-group button {
  flex: 1;
  background: #0a111c;
  border: 1px solid #1a3a5f;
  color: #a1b8d2;
  padding: 8px;
  font-size: 12px;
  cursor: pointer;
  transition: 0.3s;
}
.btn-group button.active { border-color: var(--primary); color: var(--primary); background: rgba(0,229,255,0.1); }

.placeholder { text-align: center; }
.badge { background: var(--primary); color: #000; display: inline-block; padding: 2px 8px; font-size: 10px; font-weight: 800; margin-bottom: 15px; }
.placeholder p { font-size: 13px; color: #3d5875; }

.preview-img, .preview-video { width: 100%; height: 100%; object-fit: contain; }
.live-stream { object-fit: cover; background: #000; }

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

.controls .accent-btn { width: 100%; border-radius: 2px; }

.right-analytics { height: 500px; }
.scrollable { overflow-y: auto; }

.empty-notif { height: 100%; display: flex; align-items: center; justify-content: center; color: #2d333b; font-size: 14px; font-style: italic; text-align: center; padding: 40px; }

.report-box { padding: 10px; animation: slideIn 0.5s ease; }
@keyframes slideIn { from { opacity: 0; transform: translateX(20px); } }

.report-info { font-size: 11px; color: #ff6b6b; margin-bottom: 20px; font-family: monospace; display: flex; align-items: center; gap: 10px; }
.report-info .chip { background: #ff4d4d; color: #fff; padding: 2px 6px; border-radius: 2px; }

.text-content { font-size: 15px; color: #d1dcf0; line-height: 1.8; white-space: pre-wrap; font-family: 'PingFang SC', sans-serif; }

.report-footer { margin-top: 30px; border-top: 1px solid #1a3a5f; padding-top: 15px; font-family: monospace; font-size: 10px; color: #3d5875; text-align: center; }

.dna-spinner { display: flex; justify-content: center; align-items: center; height: 300px; gap: 10px; }
.dna-spinner .dot { width: 12px; height: 12px; background: var(--primary); border-radius: 50%; animation: orbit 1s infinite alternate; }
.dna-spinner .dot:nth-child(2) { animation-delay: 0.2s; }
.dna-spinner .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes orbit { from { transform: scale(0.5); opacity: 0.2; transform: translateY(-20px); } to { transform: scale(1.2); opacity: 1; transform: translateY(20px); } }
</style>
