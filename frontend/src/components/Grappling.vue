<<<<<<< HEAD
﻿<script setup>
import { onBeforeUnmount, ref } from 'vue'

import { analyzeWithV1Fallback, analyzeWithV2 } from '../utils/api'
import { settingsStore } from '../stores/settings'
=======
<script setup>
import { onBeforeUnmount, ref } from 'vue'

import { buildApiUrl, readApiPayload } from '../utils/api'
>>>>>>> origin/main

const fileInput = ref(null)
const selectedFile = ref(null)
const previewUrl = ref(null)
const isVideo = ref(false)
<<<<<<< HEAD
const mode = ref('COMBAT_SCORING')
const isAnalyzing = ref(false)
const capturedImage = ref(null)
const feedback = ref('')
const v2Result = ref(null)

=======
const mode = ref('COMBAT_FIGHT')
const isAnalyzing = ref(false)
const capturedImage = ref(null)
const feedback = ref('')

// 摄像头相关
>>>>>>> origin/main
const cameraActive = ref(false)
const videoElement = ref(null)
const mediaStream = ref(null)
const canvasElement = ref(null)
<<<<<<< HEAD
const sourceSettings = settingsStore.settings
let recognitionInterval = null
=======
let recognitionInterval = null
let lastRecognizedTime = 0
const ACTION_CHANGE_INTERVAL = 2000
>>>>>>> origin/main

const revokePreview = () => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = null
  }
}

<<<<<<< HEAD
const onFileChange = (event) => {
  const [file] = event.target.files || []
=======
const onFileChange = (e) => {
  const [file] = e.target.files || []
>>>>>>> origin/main
  if (file) {
    stopCamera()
    revokePreview()
    selectedFile.value = file
    isVideo.value = file.type.startsWith('video/')
    previewUrl.value = URL.createObjectURL(file)
    capturedImage.value = null
    feedback.value = ''
<<<<<<< HEAD
    v2Result.value = null
=======
>>>>>>> origin/main
  }
}

const startCamera = async () => {
<<<<<<< HEAD
  if (sourceSettings.sourceType === 'rtsp') {
    alert('当前设置为 RTSP 视频流，请先在系统设置中确认 RTSP 地址。')
    return
  }

  try {
    const videoConstraints = sourceSettings.cameraDeviceId
      ? { deviceId: { exact: sourceSettings.cameraDeviceId }, width: { ideal: 1280 }, height: { ideal: 720 } }
      : { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }

    const stream = await navigator.mediaDevices.getUserMedia({ video: videoConstraints })

=======
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
    })
>>>>>>> origin/main
    mediaStream.value = stream
    cameraActive.value = true
    capturedImage.value = null
    feedback.value = ''
<<<<<<< HEAD
    v2Result.value = null

=======
    
>>>>>>> origin/main
    setTimeout(() => {
      if (videoElement.value) {
        videoElement.value.srcObject = stream
      }
    }, 100)
<<<<<<< HEAD

    startContinuousRecognition()
  } catch (error) {
    console.error('摄像头启动失败', error)
    alert(`无法启动摄像头: ${error.message}`)
=======
    
    startContinuousRecognition()
  } catch (error) {
    console.error('摄像头启动失败:', error)
    alert('无法启动摄像头: ' + error.message)
>>>>>>> origin/main
  }
}

const stopCamera = () => {
  if (recognitionInterval) {
    clearInterval(recognitionInterval)
    recognitionInterval = null
  }
<<<<<<< HEAD

  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach((track) => track.stop())
    mediaStream.value = null
  }

=======
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop())
    mediaStream.value = null
  }
>>>>>>> origin/main
  cameraActive.value = false
}

const startContinuousRecognition = () => {
<<<<<<< HEAD
  if (recognitionInterval) {
    clearInterval(recognitionInterval)
  }

  recognitionInterval = setInterval(async () => {
    if (!videoElement.value || !canvasElement.value || isAnalyzing.value || !cameraActive.value) return

    const video = videoElement.value
    if (video.readyState !== 4) return

    const canvas = canvasElement.value
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const context = canvas.getContext('2d')
    context.drawImage(video, 0, 0)

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.85))
    const frameFile = new File([blob], 'frame.jpg', { type: 'image/jpeg' })

    try {
      const { ok, data } = await analyzeWithV2({ file: frameFile, legacyMode: mode.value })
      if (ok) {
        v2Result.value = data
        capturedImage.value = URL.createObjectURL(blob)
        feedback.value = ''
      }
    } catch (error) {
      console.error('连续识别失败:', error)
=======
  if (recognitionInterval) clearInterval(recognitionInterval)
  
  recognitionInterval = setInterval(async () => {
    if (!videoElement.value || !canvasElement.value || isAnalyzing.value || !cameraActive.value) return
    
    const video = videoElement.value
    if (video.readyState !== 4) return
    
    const canvas = canvasElement.value
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0)
    
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.8))
    const formData = new FormData()
    formData.append('file', new File([blob], 'frame.jpg', { type: 'image/jpeg' }))
    formData.append('mode', mode.value)
    
    try {
      const res = await fetch(buildApiUrl('/api/analyze-vision'), {
        method: 'POST',
        body: formData
      })
      const data = await readApiPayload(res)
      if (res.ok && data.result) {
        const now = Date.now()
        capturedImage.value = URL.createObjectURL(blob)
        feedback.value = data.result
        lastRecognizedTime = now
        
        setTimeout(() => {
          if (lastRecognizedTime === now && capturedImage.value && cameraActive.value) {
            capturedImage.value = null
          }
        }, ACTION_CHANGE_INTERVAL)
      }
    } catch (error) {
      console.error('识别失败:', error)
>>>>>>> origin/main
    }
  }, 1000)
}

onBeforeUnmount(() => {
  stopCamera()
  revokePreview()
})

const triggerAnalysis = async () => {
  if (!selectedFile.value) return
<<<<<<< HEAD

  isAnalyzing.value = true
  capturedImage.value = previewUrl.value
  feedback.value = ''
  v2Result.value = null

  try {
    const v2 = await analyzeWithV2({ file: selectedFile.value, legacyMode: mode.value })
    if (v2.ok) {
      v2Result.value = v2.data
      return
    }

    const v1 = await analyzeWithV1Fallback({ file: selectedFile.value, legacyMode: mode.value })
    if (v1.ok) {
      feedback.value = v1.data.result || ''
    } else {
      feedback.value = `识别失败: ${v1.data.detail || '请更换更清晰的训练画面后重试。'}`
    }
  } catch (error) {
    feedback.value = `通信超时: ${error.message}`
=======
  
  isAnalyzing.value = true
  capturedImage.value = previewUrl.value
  feedback.value = ''
  
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('mode', mode.value)

  try {
    const res = await fetch(buildApiUrl('/api/analyze-vision'), {
      method: 'POST',
      body: formData
    })
    const data = await readApiPayload(res)
    if (res.ok) {
      feedback.value = data.result
    } else {
      feedback.value = `❌ 识别失败: ${data.detail || '请更换更清晰的训练画面后重试。'}`
    }
  } catch (error) {
    feedback.value = `❌ 通讯超时：${error.message}`
>>>>>>> origin/main
  } finally {
    isAnalyzing.value = false
  }
}
<<<<<<< HEAD

const combat = () => v2Result.value?.combat
const meta = () => v2Result.value?.meta
=======
>>>>>>> origin/main
</script>

<template>
  <div class="grappling-container">
    <div class="header-row">
<<<<<<< HEAD
      <h1>格斗技战术评估 / COMBAT AI</h1>
      <div class="status-indicator">
        <span class="label">SKELETON_PIPELINE</span>
        <span class="val">ACTIVE</span>
      </div>
    </div>

    <div class="grid-layout">
      <div class="panel left-capture">
        <div class="panel-header">实战画面输入 / INPUT</div>
        <div class="upload-area" @click="fileInput.click()">
          <div v-if="!previewUrl && !capturedImage" class="placeholder">
            <div class="badge">SENSING</div>
            <p>上传图片或视频，输出动作-效果-原因-建议四元组</p>
          </div>
          <img v-if="capturedImage" :src="capturedImage" alt="识别画面" class="preview-img" />
          <img v-else-if="previewUrl && !isVideo" :src="previewUrl" class="preview-img" />
          <video v-else-if="previewUrl && isVideo" :src="previewUrl" class="preview-video" autoplay loop muted playsinline></video>
          <video v-if="cameraActive" ref="videoElement" autoplay playsinline class="preview-video"></video>
          <canvas ref="canvasElement" style="display: none;"></canvas>
          <input type="file" ref="fileInput" @change="onFileChange" hidden accept="image/*,video/*" />
        </div>

        <div class="camera-btns" v-if="!selectedFile">
          <div class="mode-tip">当前视频源：{{ sourceSettings.sourceType === 'camera' ? '本地摄像头' : 'RTSP 视频流' }}</div>
          <button v-if="!cameraActive" class="btn accent-btn" @click.stop="startCamera" :disabled="sourceSettings.sourceType !== 'camera'">开启摄像头</button>
          <button v-else class="btn accent-btn" @click.stop="stopCamera">关闭摄像头</button>
        </div>

        <div class="mode-selector-panel">
          <div class="label">分析模式</div>
          <div class="btn-group">
            <button :class="{active: mode === 'COMBAT_FIGHT'}" @click="mode = 'COMBAT_FIGHT'">动作识别</button>
            <button :class="{active: mode === 'COMBAT_SCORING'}" @click="mode = 'COMBAT_SCORING'">全量分析</button>
          </div>
        </div>

        <div class="controls">
          <button class="btn accent-btn" @click="triggerAnalysis" :disabled="!previewUrl || isAnalyzing">
            <span v-if="!isAnalyzing">执行结构化评估</span>
            <span v-else>神经网络推理中...</span>
          </button>
        </div>
      </div>

      <div class="panel right-analytics scrollable">
        <div class="panel-header">格斗四元组 / COMBAT QUARTETS</div>

        <template v-if="combat()">
          <div class="report-info">人数 {{ meta()?.persons || 0 }} / 设备 {{ meta()?.device || '-' }} / 延迟 {{ meta()?.latency_ms?.toFixed?.(1) || 0 }}ms</div>

          <div class="block">
            <h3>动作识别</h3>
            <ul v-if="combat().actions?.length">
              <li v-for="item in combat().actions" :key="item.frame_index + '-' + item.action">
                帧 {{ item.frame_index }} - {{ item.action }} ({{ item.confidence.toFixed(2) }})
              </li>
            </ul>
            <div v-else>未检测到明显格斗动作。</div>
          </div>

          <div class="block">
            <h3>四元组列表</h3>
            <table class="qt-table" v-if="combat().quartets?.length">
              <thead>
                <tr><th>动作</th><th>效果</th><th>原因</th><th>建议</th></tr>
              </thead>
              <tbody>
                <tr v-for="(q, idx) in combat().quartets" :key="idx">
                  <td>{{ q.action }}</td>
                  <td>{{ q.effect }}</td>
                  <td>{{ q.reason }}</td>
                  <td>{{ q.suggestion }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else>暂无四元组结果。</div>
          </div>

          <div class="block">
            <h3>命中事件</h3>
            <ul v-if="combat().hit_events?.length">
              <li v-for="(h, idx) in combat().hit_events" :key="idx">
                A{{ h.attacker_id }} -> B{{ h.defender_id }}: {{ h.target }} ({{ h.confidence.toFixed(2) }})
              </li>
            </ul>
            <div v-else>未识别到明确命中事件。</div>
          </div>

          <div class="block">
            <h3>体力与稳定性</h3>
            <div>体力等级: {{ combat().fatigue.level }} ({{ combat().fatigue.score.toFixed(2) }})</div>
            <div>体力原因: {{ combat().fatigue.reason }}</div>
            <div>稳定性: {{ combat().stability.toFixed(2) }}</div>
          </div>
        </template>

        <div v-else-if="feedback" class="text-content">{{ feedback }}</div>

        <div v-else-if="isAnalyzing" class="dna-spinner">
          <div class="dot"></div><div class="dot"></div><div class="dot"></div>
        </div>

        <div v-else class="empty-notif">等待输入视频/图像进行格斗分析...</div>
=======
      <h1>🥋 擒拿格斗技战术评分 / COMBAT AI</h1>
      <div class="status-indicator">
         <span class="label">SKELETON_ENGINE</span>
         <span class="val">ACTIVE_99.1%</span>
      </div>
    </div>
    
    <div class="grid-layout">
      <div class="panel left-capture">
         <div class="panel-header">实战画面截帧 / COMBAT FRAME CAPTURE</div>
         <div class="upload-area" @click="fileInput.click()">
            <div v-if="!previewUrl && !capturedImage" class="placeholder">
               <div class="badge">SENSING</div>
               <p>放入训练图片或视频进行多维动作分析</p>
            </div>
            <img v-if="capturedImage" :src="capturedImage" alt="识别画面" class="preview-img" />
            <img v-else-if="previewUrl && !isVideo" :src="previewUrl" class="preview-img" />
            <video v-else-if="previewUrl && isVideo" :src="previewUrl" class="preview-video" autoplay loop muted playsinline></video>
            <video v-if="cameraActive" ref="videoElement" autoplay playsinline class="preview-video"></video>
            <canvas ref="canvasElement" style="display: none;"></canvas>
            <input type="file" ref="fileInput" @change="onFileChange" hidden accept="image/*,video/*" />
         </div>

         <div class="camera-btns" v-if="!selectedFile">
            <button v-if="!cameraActive" class="btn accent-btn" @click.stop="startCamera">启动摄像头</button>
            <button v-else class="btn accent-btn" @click.stop="stopCamera">关闭摄像头</button>
         </div>

         <div class="mode-selector-panel">
            <div class="label">分析模式选择 / SELECT MODE</div>
            <div class="btn-group">
                <button :class="{active: mode==='COMBAT_FIGHT'}" @click="mode='COMBAT_FIGHT'">暴力识别 (FightDetect)</button>
                <button :class="{active: mode==='COMBAT_SCORING'}" @click="mode='COMBAT_SCORING'">对抗评分 (UFC Logic)</button>
            </div>
            <div class="mode-tip">上传视频时，系统会自动抽取多帧综合识别；评分结果会重点输出双方动作和可能伤害。</div>
         </div>
         
         <div class="controls">
            <button class="btn accent-btn" @click="triggerAnalysis" :disabled="!previewUrl || isAnalyzing">
               <span v-if="!isAnalyzing">执行多维评估指令</span>
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
>>>>>>> origin/main
      </div>
    </div>
  </div>
</template>

<style scoped>
<<<<<<< HEAD
.grappling-container { animation: fadeIn 0.4s ease; height: 100%; display: flex; flex-direction: column; }
=======
.grappling-container { animation: fadeIn 0.4s ease; }
>>>>>>> origin/main
.header-row { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 30px; }
.status-indicator { font-family: monospace; font-size: 10px; background: #000; border: 1px solid var(--border); padding: 5px 12px; }
.status-indicator .label { color: #5c7694; margin-right: 10px; }
.status-indicator .val { color: var(--primary); font-weight: bold; }
<<<<<<< HEAD
.grid-layout { display: grid; grid-template-columns: minmax(380px, 44%) minmax(0, 1fr); gap: 24px; align-items: start; flex: 1; min-height: 0; }
.panel-header { border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 25px; font-size: 11px; text-transform: uppercase; color: var(--primary); letter-spacing: 2px; }
.upload-area { width: 100%; aspect-ratio: 16/10; background: rgba(0,0,0,0.5); border: 1px solid #1a3a5f; margin-bottom: 20px; cursor: pointer; display: flex; justify-content: center; align-items: center; position: relative; overflow: hidden; }
.upload-area::after { content: ''; position: absolute; inset: 10px; border: 1px solid rgba(0,229,255,0.05); pointer-events: none; }
=======

.grid-layout { display: grid; grid-template-columns: 480px 1fr; gap: 30px; align-items: start; }

.panel-header { border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 25px; font-size: 11px; text-transform: uppercase; color: var(--primary); letter-spacing: 2px; }

.upload-area {
  width: 100%; aspect-ratio: 16/10;
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
.upload-area::after { content: ''; position: absolute; inset: 10px; border: 1px solid rgba(0,229,255,0.05); pointer-events: none; }

>>>>>>> origin/main
.mode-selector-panel { margin-bottom: 25px; }
.mode-selector-panel .label { font-size: 11px; color: #5c7694; margin-bottom: 10px; font-weight: bold; }
.mode-tip { margin-top: 10px; font-size: 12px; color: #7d92ab; }
.btn-group { display: flex; gap: 10px; }
<<<<<<< HEAD
.btn-group button { flex: 1; background: #0a111c; border: 1px solid #1a3a5f; color: #a1b8d2; padding: 8px; font-size: 12px; cursor: pointer; transition: 0.3s; }
.btn-group button.active { border-color: var(--primary); color: var(--primary); background: rgba(0,229,255,0.1); }
.placeholder { text-align: center; }
.badge { background: var(--primary); color: #000; display: inline-block; padding: 2px 8px; font-size: 10px; font-weight: 800; margin-bottom: 15px; }
.placeholder p { font-size: 13px; color: #3d5875; }
.preview-img, .preview-video { width: 100%; height: 100%; object-fit: contain; }
.controls .accent-btn { width: 100%; border-radius: 2px; }
.right-analytics { height: 100%; min-height: 420px; }
.scrollable { overflow-y: auto; }
.empty-notif { height: 100%; display: flex; align-items: center; justify-content: center; color: #2d333b; font-size: 14px; font-style: italic; text-align: center; padding: 40px; }
.report-info { font-size: 12px; color: #8aa5c2; margin-bottom: 10px; }
.block { margin-top: 12px; border-top: 1px dashed #1a3a5f; padding-top: 10px; }
.block h3 { margin: 0 0 8px; font-size: 13px; color: var(--primary); }
.block ul { margin: 0; padding-left: 18px; }
.block li { margin: 4px 0; color: #d1dcf0; font-size: 13px; }
.qt-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.qt-table th, .qt-table td { border: 1px solid #1a3a5f; padding: 6px; text-align: left; vertical-align: top; color: #d1dcf0; }
.text-content { font-size: 15px; color: #d1dcf0; line-height: 1.8; white-space: pre-wrap; font-family: 'PingFang SC', sans-serif; }
=======
.btn-group button { 
  flex: 1; background: #0a111c; border: 1px solid #1a3a5f; color: #a1b8d2; 
  padding: 8px; font-size: 12px; cursor: pointer; transition: 0.3s;
}
.btn-group button.active { border-color: var(--primary); color: var(--primary); background: rgba(0,229,255,0.1); }

.placeholder { text-align: center; }
.badge { background: var(--primary); color: #000; display: inline-block; padding: 2px 8px; font-size: 10px; font-weight: 800; margin-bottom: 15px; }
.placeholder p { font-size: 13px; color: #3d5875; }

.preview-img, .preview-video { width: 100%; height: 100%; object-fit: contain; }

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

>>>>>>> origin/main
.dna-spinner { display: flex; justify-content: center; align-items: center; height: 300px; gap: 10px; }
.dna-spinner .dot { width: 12px; height: 12px; background: var(--primary); border-radius: 50%; animation: orbit 1s infinite alternate; }
.dna-spinner .dot:nth-child(2) { animation-delay: 0.2s; }
.dna-spinner .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes orbit { from { transform: scale(0.5); opacity: 0.2; transform: translateY(-20px); } to { transform: scale(1.2); opacity: 1; transform: translateY(20px); } }
<<<<<<< HEAD
@media (max-width: 1080px) { .grid-layout { grid-template-columns: 1fr; } }
</style>

=======
</style>
>>>>>>> origin/main
