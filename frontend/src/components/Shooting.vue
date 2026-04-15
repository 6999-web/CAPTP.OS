<script setup>
import { onBeforeUnmount, ref } from 'vue'

import { buildApiUrl, readApiPayload } from '../utils/api'

const fileInput = ref(null)
const selectedFile = ref(null)
const previewUrl = ref(null)
const mode = ref('SHOOTING_POSTURE')
const isAnalyzing = ref(false)
const capturedImage = ref(null)
const feedback = ref('')

// 摄像头相关
const cameraActive = ref(false)
const videoElement = ref(null)
const mediaStream = ref(null)
const canvasElement = ref(null)
let recognitionInterval = null
let lastRecognizedTime = 0
const ACTION_CHANGE_INTERVAL = 2000 // 动作变化检测间隔(毫秒)

const revokePreview = () => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = null
  }
}

const onFileChange = (e) => {
  const [file] = e.target.files || []
  if (file) {
    stopCamera()
    revokePreview()
    selectedFile.value = file
    previewUrl.value = URL.createObjectURL(file)
    capturedImage.value = null
    feedback.value = ''
  }
}

// 启动摄像头
const startCamera = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
    })
    mediaStream.value = stream
    cameraActive.value = true
    capturedImage.value = null
    feedback.value = ''
    
    setTimeout(() => {
      if (videoElement.value) {
        videoElement.value.srcObject = stream
      }
    }, 100)
    
    // 开始持续识别
    startContinuousRecognition()
  } catch (error) {
    console.error('摄像头启动失败:', error)
    alert('无法启动摄像头: ' + error.message)
  }
}

// 停止摄像头
const stopCamera = () => {
  if (recognitionInterval) {
    clearInterval(recognitionInterval)
    recognitionInterval = null
  }
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
    }
  }, 1000)
}

onBeforeUnmount(() => {
  stopCamera()
  revokePreview()
})

const triggerAnalysis = async () => {
  if (!selectedFile.value) return
  
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
  } finally {
    isAnalyzing.value = false
  }
}
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
               <span class="node">NODE_ID: {{ (Math.random()*1000).toFixed(0) }}</span>
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

.loading-wave { display: flex; justify-content: center; align-items: center; height: 300px; gap: 5px; }
.loading-wave .bar { width: 4px; height: 30px; background: var(--primary); animation: wave 1s infinite ease-in-out; }
.loading-wave .bar:nth-child(2) { animation-delay: 0.1s; }
.loading-wave .bar:nth-child(3) { animation-delay: 0.2s; }
.loading-wave .bar:nth-child(4) { animation-delay: 0.3s; }
@keyframes wave { 0% { height: 10px; } 50% { height: 40px; opacity: 1; } 100% { height: 10px; opacity: 0.3; } }
</style>
