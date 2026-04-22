<<<<<<< HEAD
﻿<script setup>
import { onBeforeUnmount, ref } from 'vue'

import { analyzeWithV1Fallback, analyzeWithV2, buildWsUrl } from '../utils/api'
import { settingsStore } from '../stores/settings'
=======
<script setup>
import { onBeforeUnmount, ref } from 'vue'

import { buildApiUrl, readApiPayload } from '../utils/api'
>>>>>>> origin/main

const fileInput = ref(null)
const selectedFile = ref(null)
const previewUrl = ref(null)
const mode = ref('SHOOTING_POSTURE')
const isAnalyzing = ref(false)
const capturedImage = ref(null)
const feedback = ref('')
<<<<<<< HEAD
const v2Result = ref(null)

=======

// 摄像头相关
>>>>>>> origin/main
const cameraActive = ref(false)
const videoElement = ref(null)
const mediaStream = ref(null)
const canvasElement = ref(null)
<<<<<<< HEAD
const sourceSettings = settingsStore.settings

const wsConnected = ref(false)
const trainingStage = ref('A_RECEIVE_WEAPON')
const successHint = ref('')
const errorCards = ref([])

let recognitionInterval = null
let successFlashTimer = null
let frameCursor = 0
let lastFlowStageSent = ''
let wsConnection = null
=======
let recognitionInterval = null
let lastRecognizedTime = 0
const ACTION_CHANGE_INTERVAL = 2000 // 动作变化检测间隔(毫秒)
>>>>>>> origin/main

const revokePreview = () => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = null
  }
}

<<<<<<< HEAD
const upsertErrorCard = (card) => {
  const idx = errorCards.value.findIndex((item) => item.id === card.id)
  if (idx >= 0) {
    errorCards.value[idx] = card
    return
  }
  errorCards.value.unshift(card)
}

const removeErrorCard = (id) => {
  errorCards.value = errorCards.value.filter((item) => item.id !== id)
}

const flashSuccess = (text) => {
  successHint.value = text
  if (successFlashTimer) clearTimeout(successFlashTimer)
  successFlashTimer = setTimeout(() => {
    successHint.value = ''
  }, 1800)
}

const toDataUrl = (blob) => new Promise((resolve, reject) => {
  const reader = new FileReader()
  reader.onload = () => resolve(reader.result)
  reader.onerror = reject
  reader.readAsDataURL(blob)
})

const mapFlowStageToActions = (flowStage) => {
  const map = {
    pass_gun_method_1: ['remove_mag'],
    pass_gun_method_2: ['check_chamber'],
    check_weapon: ['safe_on'],
    insert_magazine: ['insert_mag', 'holster_or_ready'],
    prepare_and_fire: ['draw', 'iso_grip', 'rack_slide', 'fire'],
    post_fire_check: ['final_remove_mag', 'final_check_chamber']
  }
  return map[flowStage] || []
}

const handleStandardImageError = (event) => {
  if (!event?.target) return
  if (event.target.dataset.fallbackApplied === '1') return
  event.target.dataset.fallbackApplied = '1'
  event.target.src = '/school_badge.jpg'
}

const connectCoachSocket = () => {
  if (wsConnection) return
  try {
    wsConnection = new WebSocket(buildWsUrl('/api/v2/stream/shooting-coach'))
    wsConnection.onopen = () => {
      wsConnected.value = true
    }
    wsConnection.onclose = () => {
      wsConnected.value = false
      wsConnection = null
    }
    wsConnection.onerror = () => {
      wsConnected.value = false
    }
    wsConnection.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data)
        if (msg.event === 'error:add' || msg.event === 'error:update') upsertErrorCard(msg.data)
        if (msg.event === 'error:remove') removeErrorCard(msg.data.id)
        if (msg.event === 'hint:success') flashSuccess(msg.data.text || '动作已纠正')
        if (msg.event === 'stage:update') trainingStage.value = msg.data.stage || trainingStage.value
      } catch (error) {
        console.warn('教练流消息解析失败', error)
      }
    }
  } catch (error) {
    console.error('连接教练流失败', error)
  }
}

const closeCoachSocket = () => {
  if (!wsConnection) return
  wsConnection.close()
  wsConnection = null
  wsConnected.value = false
}

const pushCoachPacket = async (blob, v2Data) => {
  if (!wsConnection || wsConnection.readyState !== WebSocket.OPEN || !v2Data?.shooting) return
  const frameDataUrl = await toDataUrl(blob)
  const shooting = v2Data.shooting

  const actions = shooting.flow_stage && shooting.flow_stage !== lastFlowStageSent
    ? mapFlowStageToActions(shooting.flow_stage)
    : []
  if (shooting.flow_stage) {
    lastFlowStageSent = shooting.flow_stage
  }

  wsConnection.send(JSON.stringify({
    event: 'frame',
    frame: frameDataUrl,
    frame_index: frameCursor++,
    actions,
    shooting: {
      posture_compliance: shooting.posture_compliance,
      flow_order_ok: shooting.flow_order_ok,
      flow_stage: shooting.flow_stage,
      violations: shooting.violations || []
    }
  }))
}

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
    previewUrl.value = URL.createObjectURL(file)
    capturedImage.value = null
    feedback.value = ''
<<<<<<< HEAD
    v2Result.value = null
  }
}

const startCamera = async () => {
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
  }
}

// 启动摄像头
const startCamera = async () => {
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
    errorCards.value = []
    trainingStage.value = 'A_RECEIVE_WEAPON'
    frameCursor = 0
    lastFlowStageSent = ''

=======
    
>>>>>>> origin/main
    setTimeout(() => {
      if (videoElement.value) {
        videoElement.value.srcObject = stream
      }
    }, 100)
<<<<<<< HEAD

    connectCoachSocket()
    startContinuousRecognition()
  } catch (error) {
    console.error('摄像头启动失败', error)
    alert(`无法启动摄像头: ${error.message}`)
  }
}

=======
    
    // 开始持续识别
    startContinuousRecognition()
  } catch (error) {
    console.error('摄像头启动失败:', error)
    alert('无法启动摄像头: ' + error.message)
  }
}

// 停止摄像头
>>>>>>> origin/main
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

  cameraActive.value = false
  closeCoachSocket()
}

const callV2ByBlob = async (blob) => {
  const frameFile = new File([blob], 'frame.jpg', { type: 'image/jpeg' })
  const { ok, data } = await analyzeWithV2({ file: frameFile, legacyMode: mode.value })
  if (!ok) return null
  return data
}

const startContinuousRecognition = () => {
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

    try {
      const data = await callV2ByBlob(blob)
      if (data) {
        capturedImage.value = URL.createObjectURL(blob)
        v2Result.value = data
        feedback.value = ''
        await pushCoachPacket(blob, data)
      }
    } catch (error) {
      console.error('连续识别失败:', error)
=======
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop())
    mediaStream.value = null
  }
  cameraActive.value = false
}

// 持续识别
const startContinuousRecognition = () => {
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
        // 识别到动作，定格显示
        capturedImage.value = URL.createObjectURL(blob)
        feedback.value = data.result
        lastRecognizedTime = now
        
        // 动作变化后恢复实时视频
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
<<<<<<< HEAD
  if (successFlashTimer) clearTimeout(successFlashTimer)
=======
>>>>>>> origin/main
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
      feedback.value = `识别失败: ${v1.data.detail || '请检查输入内容。'}`
    }
  } catch (error) {
    feedback.value = `网络通信超时: ${error.message}`
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
      feedback.value = `⚠️ 识别失败: ${data.detail || '请检查图片清晰度后重试。'}`
    }
  } catch (error) {
    feedback.value = `❌ 骨干网络通讯超时: ${error.message}`
>>>>>>> origin/main
  } finally {
    isAnalyzing.value = false
  }
}
<<<<<<< HEAD

const shooting = () => v2Result.value?.shooting
const meta = () => v2Result.value?.meta
=======
>>>>>>> origin/main
</script>

<template>
  <div class="shooting-container">
    <div class="page-title row">
      <div class="title-main">
<<<<<<< HEAD
        <h1>射击技战术智能评估 / MARKSMANSHIP AI</h1>
        <p>结构化输出：姿势合规、流程阶段、违规清单、证据帧。</p>
      </div>
      <div class="engine-badge">
        <span class="label">CV PIPELINE</span>
        <span class="version">V2</span>
=======
        <h1>🎯 射击技战术智能评估 / MARKSMANSHIP AI</h1>
        <p>基于跨模态视觉大模型实现高精度弹着点预测与持枪规范度诊断</p>
      </div>
      <div class="engine-badge">
        <span class="label">NVIDIA NIM </span>
        <span class="version">LLAMA-3.2-90B</span>
>>>>>>> origin/main
      </div>
    </div>

    <div class="main-split">
      <div class="panel upload-panel">
        <div class="panel-header">数据源输入 / DATA SOURCE</div>
<<<<<<< HEAD
        <div class="upload-box" @click="!cameraActive && fileInput.click()">
          <video v-if="cameraActive" ref="videoElement" autoplay playsinline class="preview-video"></video>
          <img v-else-if="capturedImage" :src="capturedImage" alt="识别画面" class="preview-img" />
          <img v-else-if="previewUrl" :src="previewUrl" alt="预览" class="preview-img" />
          <div v-else class="upload-placeholder">
            <span class="icon">+</span>
            <p>点击选择图像/视频进行分析</p>
            <div class="hint">支持 JPG / PNG / MP4 / AVI</div>
          </div>
          <canvas ref="canvasElement" style="display: none;"></canvas>
          <input type="file" ref="fileInput" @change="onFileChange" hidden accept="image/*,video/*" />
        </div>

        <div class="camera-status">
          <div class="selector-label">当前视频源 / SOURCE</div>
          <div class="mode-tip">{{ sourceSettings.sourceType === 'camera' ? '本地摄像头' : 'RTSP 视频流（在设置中统一配置）' }}</div>
          <div class="camera-btns">
            <button v-if="!cameraActive" class="btn tiny-btn" @click.stop="startCamera" :disabled="sourceSettings.sourceType !== 'camera'">开启摄像头</button>
            <button v-else class="btn tiny-btn" @click.stop="stopCamera">关闭摄像头</button>
          </div>
          <div class="ws-state" :class="{ online: wsConnected }">教练流 {{ wsConnected ? '已连接' : '未连接' }}</div>
        </div>

        <div class="mode-selector">
          <div class="selector-label">选择分析模式 / INFERENCE MODE</div>
          <div class="option-grid">
            <label :class="{ selected: mode === 'SHOOTING_POSTURE' }">
              <input type="radio" v-model="mode" value="SHOOTING_POSTURE" hidden /> 姿势合规
            </label>
            <label :class="{ selected: mode === 'SHOOTING_TARGET' }">
              <input type="radio" v-model="mode" value="SHOOTING_TARGET" hidden /> 流程识别
            </label>
            <label :class="{ selected: mode === 'SHOOTING_WEAPON' }">
              <input type="radio" v-model="mode" value="SHOOTING_WEAPON" hidden /> 枪械安全
            </label>
          </div>
        </div>

        <button class="btn full-width" @click="triggerAnalysis" :disabled="!previewUrl || isAnalyzing">
          <span v-if="!isAnalyzing">启动结构化评估</span>
          <span v-else class="analyzing-state">系统推理中...</span>
=======
        <div class="upload-box" @click="fileInput.click()">
           <div v-if="!previewUrl && !capturedImage" class="upload-placeholder">
              <span class="icon">📁</span>
              <p>点击选择或拖拽图片进行侦测</p>
              <div class="hint">支持 JPG/PNG/BMP 格式</div>
           </div>
           <img v-if="capturedImage" :src="capturedImage" alt="识别画面" class="preview-img" />
           <img v-else-if="previewUrl" :src="previewUrl" alt="预览" class="preview-img" />
           <video v-if="cameraActive" ref="videoElement" autoplay playsinline class="preview-video"></video>
           <canvas ref="canvasElement" style="display: none;"></canvas>
           <input type="file" ref="fileInput" @change="onFileChange" hidden accept="image/*" />
        </div>

        <div class="mode-selector">
           <div class="selector-label">选择分析模态 / INFERENCE MODE</div>
           <div class="mode-tip">建议上传正面、清晰、靶纸主体占比较高的图片；靶纸模式会返回具体环数、分布和水平判断。</div>
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

        <button class="btn full-width" @click="triggerAnalysis" :disabled="!previewUrl || isAnalyzing">
           <span v-if="!isAnalyzing">启动 AI 侦测评估</span>
           <span v-else class="analyzing-state">系统中枢运算中...</span>
>>>>>>> origin/main
        </button>
      </div>

      <div class="panel result-panel h-scroll">
<<<<<<< HEAD
        <div class="panel-header">结构化结果 / STRUCTURED OUTPUT</div>

        <div class="stage-line">
          <span>训练状态机</span>
          <b>{{ trainingStage }}</b>
        </div>

        <div v-if="successHint" class="success-flash">{{ successHint }}</div>

        <div class="block error-zone">
          <h3>实时纠错卡片</h3>
          <transition-group name="error-card" tag="div" class="error-list">
            <div v-for="card in errorCards" :key="card.id" class="error-card-item">
              <div class="error-card-head">
                <span class="tag">{{ card.type }}</span>
                <span class="reason">{{ card.reason }}</span>
              </div>
              <div class="error-grid">
                <img v-if="card.overlay_b64" :src="`data:image/jpeg;base64,${card.overlay_b64}`" alt="违规抓拍图" class="err-shot" />
                <img v-if="card.standard_ref_url" :src="card.standard_ref_url" alt="标准动作参考图" class="std-shot" @error="handleStandardImageError" />
              </div>
              <div class="hint-line">改正建议：{{ card.suggestion }}</div>
              <div v-if="card.why_wrong?.length" class="why-zone">
                <div class="why-title">为什么判错</div>
                <ul>
                  <li v-for="(item, idx) in card.why_wrong" :key="card.id + '-why-' + idx">{{ item }}</li>
                </ul>
              </div>
            </div>
          </transition-group>
          <div v-if="!errorCards.length" class="empty-tip">当前无激活错误卡片。</div>
        </div>

        <div v-if="shooting()" class="report-content">
          <div class="kv">姿势合规：<b>{{ shooting().posture_compliance ? '合规' : '不合规' }}</b> ({{ shooting().posture_score.toFixed(2) }})</div>
          <div class="kv">流程阶段：<b>{{ shooting().flow_stage }}</b></div>
          <div class="kv">顺序校验：<b>{{ shooting().flow_order_ok ? '通过' : '未通过' }}</b></div>
          <div class="kv" v-if="meta()">元信息：人数 {{ meta().persons }} / 设备 {{ meta().device }} / 延迟 {{ meta().latency_ms?.toFixed?.(1) || 0 }}ms</div>

          <div class="block">
            <h3>违规项清单</h3>
            <ul v-if="shooting().violations?.length">
              <li v-for="item in shooting().violations" :key="item.code + '-' + item.evidence_frame_idx">
                [{{ item.severity }}] {{ item.code }} - {{ item.description }} ({{ item.rule_ref }})
              </li>
            </ul>
            <div v-else>未发现明显违规项。</div>
          </div>

          <div class="block">
            <h3>流程时间轴（证据帧）</h3>
            <ul v-if="shooting().evidence?.length">
              <li v-for="item in shooting().evidence" :key="item.frame_index + '-' + item.label">
                帧 {{ item.frame_index }}: {{ item.label }} ({{ item.confidence.toFixed(2) }})
              </li>
            </ul>
            <div v-else>暂无证据帧。</div>
          </div>
        </div>

        <div v-else-if="feedback" class="report-content text-body">{{ feedback }}</div>

        <div v-else-if="isAnalyzing" class="loading-wave">
          <div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div>
        </div>

        <div v-else class="empty-state">
          <div class="p-icon">...</div>
          <p>等待分析任务</p>
        </div>
=======
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
               <span class="node">NODE_ID: {{ (Math.random()*1000).toFixed(0) }}</span>
            </div>
            <div class="text-body">{{ feedback }}</div>
            <div class="report-footer">
               数据经端到端加密传输（AES-256）
            </div>
         </div>
>>>>>>> origin/main
      </div>
    </div>
  </div>
</template>

<style scoped>
<<<<<<< HEAD
.shooting-container { animation: fadeIn 0.4s ease; height: 100%; display: flex; flex-direction: column; }
=======
.shooting-container { animation: fadeIn 0.4s ease; }
>>>>>>> origin/main
.row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.engine-badge { background: #000; border: 1px solid var(--border); padding: 5px 15px; border-radius: 4px; font-family: monospace; font-size: 11px; }
.engine-badge .label { color: #76b900; font-weight: bold; }
.engine-badge .version { color: var(--primary); margin-left: 10px; }

<<<<<<< HEAD
.main-split { display: grid; grid-template-columns: minmax(360px, 42%) minmax(0, 1fr); gap: 24px; flex: 1; min-height: 0; }
.panel-header { border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 20px; font-size: 11px; font-weight: bold; color: var(--primary); letter-spacing: 2px; }
.upload-box { width: 100%; height: 260px; background: rgba(0,0,0,0.3); border: 1px dashed #1a3a5f; border-radius: 4px; display: flex; justify-content: center; align-items: center; cursor: pointer; transition: 0.3s; overflow: hidden; margin-bottom: 25px; }
.upload-box:hover { border-color: var(--primary); background: rgba(0, 229, 255, 0.05); }
.upload-placeholder { text-align: center; }
.upload-placeholder .icon { font-size: 30px; opacity: 0.5; margin-bottom: 10px; display: block; }
.upload-placeholder p { font-size: 13px; color: var(--text-dim); margin-top: 5px; }
.preview-img, .preview-video { width: 100%; height: 100%; object-fit: contain; }
.mode-selector { margin-bottom: 30px; }
.camera-status { margin-bottom: 20px; }
.camera-btns { margin-top: 10px; }
.ws-state { margin-top: 8px; font-size: 12px; color: #8092a6; }
.ws-state.online { color: #00e676; }
.tiny-btn { padding: 8px 14px; font-size: 12px; }
.selector-label { font-size: 11px; color: #5c7694; margin-bottom: 12px; font-weight: 700; text-transform: uppercase; }
.mode-tip { margin-bottom: 12px; font-size: 12px; color: #7d92ab; }
.option-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.option-grid label { background: #0a111c; border: 1px solid #1a3a5f; padding: 12px; text-align: center; font-size: 13px; color: var(--text-dim); cursor: pointer; transition: 0.3s; }
.option-grid label.selected { border-color: var(--primary); color: var(--primary); background: rgba(0, 229, 255, 0.1); }
.full-width { width: 100%; }
.empty-state { text-align: center; margin-top: 100px; color: #2d333b; }
.empty-state .p-icon { font-size: 40px; margin-bottom: 20px; }
.report-content { color: #fff; line-height: 1.8; animation: slideUp 0.5s ease-out; }
.stage-line { display: flex; justify-content: space-between; padding: 8px 12px; border: 1px solid #1a3a5f; margin-bottom: 12px; border-radius: 4px; background: rgba(8, 16, 29, 0.75); color: #9db4cd; }
.stage-line b { color: #00cfff; }
.success-flash { background: rgba(0, 180, 80, 0.15); border: 1px solid rgba(0, 255, 136, 0.55); color: #5effaa; padding: 8px 10px; border-radius: 4px; margin-bottom: 12px; animation: glow 1s ease-in-out infinite alternate; }
.error-zone { margin-top: 0; }
.error-list { display: flex; flex-direction: column; gap: 10px; }
.error-card-item { border: 1px solid rgba(255, 80, 80, 0.45); background: rgba(61, 14, 22, 0.5); border-radius: 6px; padding: 10px; }
.error-card-head { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.error-card-head .tag { font-size: 11px; padding: 2px 7px; border-radius: 999px; border: 1px solid rgba(255, 80, 80, 0.55); color: #ff9d9d; }
.error-card-head .reason { font-size: 13px; color: #ffd8d8; }
.error-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 8px; }
.err-shot, .std-shot { width: 100%; height: 110px; object-fit: cover; border: 1px solid #24496b; border-radius: 4px; background: #05090f; }
.hint-line { font-size: 12px; color: #ffd3d3; }
.why-zone { margin-top: 8px; border-top: 1px dashed rgba(255, 128, 128, 0.35); padding-top: 6px; }
.why-title { font-size: 12px; color: #ffb4b4; margin-bottom: 4px; font-weight: 700; }
.why-zone ul { margin: 0; padding-left: 18px; }
.why-zone li { font-size: 12px; color: #ffdede; line-height: 1.5; }
.empty-tip { color: #6d86a3; font-size: 12px; }
.kv { margin-bottom: 6px; font-size: 14px; color: #d0d7de; }
.block { margin-top: 16px; border-top: 1px dashed #1a3a5f; padding-top: 12px; }
.block h3 { margin: 0 0 8px; font-size: 13px; color: var(--primary); }
.block ul { margin: 0; padding-left: 18px; }
.block li { margin: 4px 0; color: #d0d7de; font-size: 13px; }
.text-body { white-space: pre-wrap; font-size: 15px; color: #d0d7de; padding: 0 10px; }
=======
.main-split { display: grid; grid-template-columns: 450px 1fr; gap: 30px; }

.panel-header { border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 20px; font-size: 11px; font-weight: bold; color: var(--primary); letter-spacing: 2px; }

.upload-box {
  width: 100%; height: 260px;
  background: rgba(0,0,0,0.3);
  border: 1px dashed #1a3a5f;
  border-radius: 4px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: 0.3s;
  overflow: hidden;
  margin-bottom: 25px;
}
.upload-box:hover { border-color: var(--primary); background: rgba(0, 229, 255, 0.05); }

.upload-placeholder { text-align: center; }
.upload-placeholder .icon { font-size: 30px; opacity: 0.5; margin-bottom: 10px; display: block; }
.upload-placeholder p { font-size: 13px; color: var(--text-dim); margin-top: 5px; }

.preview-img { width: 100%; height: 100%; object-fit: contain; }
.preview-video { width: 100%; height: 100%; object-fit: contain; }

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

>>>>>>> origin/main
.loading-wave { display: flex; justify-content: center; align-items: center; height: 300px; gap: 5px; }
.loading-wave .bar { width: 4px; height: 30px; background: var(--primary); animation: wave 1s infinite ease-in-out; }
.loading-wave .bar:nth-child(2) { animation-delay: 0.1s; }
.loading-wave .bar:nth-child(3) { animation-delay: 0.2s; }
.loading-wave .bar:nth-child(4) { animation-delay: 0.3s; }
<<<<<<< HEAD
.error-card-enter-active, .error-card-leave-active { transition: all 0.25s ease; }
.error-card-enter-from, .error-card-leave-to { opacity: 0; transform: translateY(-6px); }
@keyframes wave { 0% { height: 10px; } 50% { height: 40px; opacity: 1; } 100% { height: 10px; opacity: 0.3; } }
@keyframes glow { from { box-shadow: 0 0 0 rgba(0, 255, 136, 0.2); } to { box-shadow: 0 0 10px rgba(0, 255, 136, 0.35); } }
@media (max-width: 1080px) {
  .main-split { grid-template-columns: 1fr; }
  .error-grid { grid-template-columns: 1fr; }
}
=======
@keyframes wave { 0% { height: 10px; } 50% { height: 40px; opacity: 1; } 100% { height: 10px; opacity: 0.3; } }
>>>>>>> origin/main
</style>
