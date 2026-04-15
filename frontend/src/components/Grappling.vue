<script setup>
import { onBeforeUnmount, ref } from 'vue'

import { buildApiUrl, readApiPayload } from '../utils/api'

const fileInput = ref(null)
const selectedFile = ref(null)
const previewUrl = ref(null)
const isVideo = ref(false)
const mode = ref('COMBAT_FIGHT')
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
const ACTION_CHANGE_INTERVAL = 2000

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
    isVideo.value = file.type.startsWith('video/')
    previewUrl.value = URL.createObjectURL(file)
    capturedImage.value = null
    feedback.value = ''
  }
}

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
    
    startContinuousRecognition()
  } catch (error) {
    console.error('摄像头启动失败:', error)
    alert('无法启动摄像头: ' + error.message)
  }
}

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
      feedback.value = `❌ 识别失败: ${data.detail || '请更换更清晰的训练画面后重试。'}`
    }
  } catch (error) {
    feedback.value = `❌ 通讯超时：${error.message}`
  } finally {
    isAnalyzing.value = false
  }
}
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

.mode-selector-panel { margin-bottom: 25px; }
.mode-selector-panel .label { font-size: 11px; color: #5c7694; margin-bottom: 10px; font-weight: bold; }
.mode-tip { margin-top: 10px; font-size: 12px; color: #7d92ab; }
.btn-group { display: flex; gap: 10px; }
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

.dna-spinner { display: flex; justify-content: center; align-items: center; height: 300px; gap: 10px; }
.dna-spinner .dot { width: 12px; height: 12px; background: var(--primary); border-radius: 50%; animation: orbit 1s infinite alternate; }
.dna-spinner .dot:nth-child(2) { animation-delay: 0.2s; }
.dna-spinner .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes orbit { from { transform: scale(0.5); opacity: 0.2; transform: translateY(-20px); } to { transform: scale(1.2); opacity: 1; transform: translateY(20px); } }
</style>
