import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

export const useLiveCameraSource = (videoRef) => {
  const liveStream = ref(null)
  const liveError = ref('')
  const liveStatus = ref('待命，尚未建立实时画面链路。')
  const cameraDevices = ref([])
  const selectedCameraId = ref('')
  const isRefreshingDevices = ref(false)

  const supportsCameraApi = () =>
    typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia

  const wait = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms))

  const stopTracks = (stream) => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop())
    }
  }

  const detachVideo = () => {
    if (videoRef.value) {
      videoRef.value.srcObject = null
    }
  }

  const listCameraDevices = async () => {
    const devices = await navigator.mediaDevices.enumerateDevices()
    const videoInputs = devices
      .filter((device) => device.kind === 'videoinput')
      .map((device, index) => ({
        id: device.deviceId,
        label: device.label || `摄像头 ${index + 1}`
      }))

    cameraDevices.value = videoInputs

    if (!videoInputs.length) {
      selectedCameraId.value = ''
      return videoInputs
    }

    const matchedDevice = videoInputs.find((device) => device.id === selectedCameraId.value)
    if (!matchedDevice) {
      selectedCameraId.value = videoInputs[0].id
    }

    return videoInputs
  }

  const refreshCameraDevices = async (ensurePermission = false) => {
    if (!supportsCameraApi()) {
      liveError.value = '当前浏览器不支持摄像头实时接入。'
      liveStatus.value = '设备接入失败。'
      return []
    }

    isRefreshingDevices.value = true

    try {
      let devices = await listCameraDevices()
      const needPermissionBootstrap = ensurePermission && devices.some((device) => /^摄像头 \d+$/.test(device.label))

      if (ensurePermission && (!devices.length || needPermissionBootstrap)) {
        const tempStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        stopTracks(tempStream)
        devices = await listCameraDevices()
      }

      if (!devices.length) {
        liveError.value = '未检测到可用摄像头，请确认本机摄像头或 Wi‑Fi 摄像头已被系统识别。'
        liveStatus.value = '设备接入失败。'
      }

      return devices
    } catch (error) {
      liveError.value = `摄像头列表获取失败：${error.message}`
      liveStatus.value = '设备接入失败。'
      return []
    } finally {
      isRefreshingDevices.value = false
    }
  }

  const bindLiveStream = async (stream) => {
    await nextTick()
    if (!videoRef.value) return

    videoRef.value.srcObject = stream
    await videoRef.value.play()
  }

  const buildVideoConstraints = (cameraId) => ({
    width: { ideal: 1280 },
    height: { ideal: 720 },
    ...(cameraId
      ? { deviceId: { exact: cameraId } }
      : { facingMode: { ideal: 'environment' } })
  })

  const stopLiveStream = (statusMessage = '实时画面已关闭。') => {
    stopTracks(liveStream.value)
    liveStream.value = null
    detachVideo()
    liveStatus.value = statusMessage
  }

  const startLiveStream = async (preferredCameraId = selectedCameraId.value) => {
    if (!supportsCameraApi()) {
      liveError.value = '当前浏览器不支持摄像头实时接入。'
      liveStatus.value = '设备接入失败。'
      return null
    }

    try {
      liveError.value = ''
      liveStatus.value = '正在建立实时画面链路...'
      await refreshCameraDevices(true)
      const targetCameraId = preferredCameraId || selectedCameraId.value

      if (liveStream.value) {
        stopTracks(liveStream.value)
        liveStream.value = null
      }

      let stream
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: buildVideoConstraints(targetCameraId),
          audio: false
        })
      } catch (error) {
        if (!targetCameraId) {
          throw error
        }

        stream = await navigator.mediaDevices.getUserMedia({
          video: buildVideoConstraints(''),
          audio: false
        })
      }

      liveStream.value = stream
      await bindLiveStream(stream)
      await refreshCameraDevices(false)

      const actualDeviceId = stream.getVideoTracks()[0]?.getSettings?.().deviceId
      if (actualDeviceId) {
        selectedCameraId.value = actualDeviceId
      }

      liveStatus.value = '实时画面已接入，可抓拍当前画面或开启连续识别。'
      return stream
    } catch (error) {
      stopTracks(liveStream.value)
      liveStream.value = null
      detachVideo()
      liveError.value = error?.name === 'NotAllowedError'
        ? '摄像头权限被拒绝，请先允许浏览器访问摄像头。'
        : `实时画面接入失败：${error.message}`
      liveStatus.value = '设备接入失败。'
      return null
    }
  }

  const switchCamera = async (cameraId) => {
    selectedCameraId.value = cameraId

    if (liveStream.value) {
      await startLiveStream(cameraId)
    }
  }

  const captureLiveFrame = async ({
    mimeType = 'image/jpeg',
    quality = 0.92,
    fileNamePrefix = 'live_capture'
  } = {}) => {
    if (!liveStream.value || !videoRef.value) {
      throw new Error('实时画面尚未开启')
    }

    const width = videoRef.value.videoWidth || 1280
    const height = videoRef.value.videoHeight || 720
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height

    const context = canvas.getContext('2d')
    context.drawImage(videoRef.value, 0, 0, width, height)

    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob(
        (imageBlob) => {
          if (imageBlob) {
            resolve(imageBlob)
          } else {
            reject(new Error('实时画面抓拍失败'))
          }
        },
        mimeType,
        quality
      )
    })

    return new File([blob], `${fileNamePrefix}_${Date.now()}.jpg`, { type: mimeType })
  }

  const captureFrameCanvas = () => {
    if (!liveStream.value || !videoRef.value) {
      throw new Error('实时画面尚未开启')
    }

    const width = videoRef.value.videoWidth || 1280
    const height = videoRef.value.videoHeight || 720
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height

    const context = canvas.getContext('2d')
    context.drawImage(videoRef.value, 0, 0, width, height)
    return canvas
  }

  const computeCanvasSharpness = (canvas) => {
    const sampleWidth = 160
    const sampleHeight = Math.max(90, Math.round(sampleWidth * (canvas.height / canvas.width)))
    const sampleCanvas = document.createElement('canvas')
    sampleCanvas.width = sampleWidth
    sampleCanvas.height = sampleHeight

    const sampleContext = sampleCanvas.getContext('2d')
    sampleContext.drawImage(canvas, 0, 0, sampleWidth, sampleHeight)
    const imageData = sampleContext.getImageData(0, 0, sampleWidth, sampleHeight).data

    let gradientSum = 0
    for (let y = 0; y < sampleHeight - 1; y += 1) {
      for (let x = 0; x < sampleWidth - 1; x += 1) {
        const index = (y * sampleWidth + x) * 4
        const rightIndex = (y * sampleWidth + (x + 1)) * 4
        const bottomIndex = ((y + 1) * sampleWidth + x) * 4

        const gray = (imageData[index] + imageData[index + 1] + imageData[index + 2]) / 3
        const grayRight = (imageData[rightIndex] + imageData[rightIndex + 1] + imageData[rightIndex + 2]) / 3
        const grayBottom = (imageData[bottomIndex] + imageData[bottomIndex + 1] + imageData[bottomIndex + 2]) / 3

        gradientSum += Math.abs(gray - grayRight) + Math.abs(gray - grayBottom)
      }
    }

    return gradientSum / (sampleWidth * sampleHeight)
  }

  const canvasToFile = async (canvas, {
    mimeType = 'image/jpeg',
    quality = 0.92,
    fileNamePrefix = 'live_capture'
  } = {}) => {
    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob(
        (imageBlob) => {
          if (imageBlob) {
            resolve(imageBlob)
          } else {
            reject(new Error('实时画面抓拍失败'))
          }
        },
        mimeType,
        quality
      )
    })

    return new File([blob], `${fileNamePrefix}_${Date.now()}.jpg`, { type: mimeType })
  }

  const captureBestFrame = async ({
    sampleCount = 3,
    intervalMs = 120,
    mimeType = 'image/jpeg',
    quality = 0.92,
    fileNamePrefix = 'live_best_capture'
  } = {}) => {
    let bestCanvas = null
    let bestScore = -1

    for (let index = 0; index < sampleCount; index += 1) {
      const canvas = captureFrameCanvas()
      const score = computeCanvasSharpness(canvas)
      if (score > bestScore) {
        bestScore = score
        bestCanvas = canvas
      }

      if (index < sampleCount - 1) {
        await wait(intervalMs)
      }
    }

    if (!bestCanvas) {
      throw new Error('无法从实时画面获取有效帧')
    }

    return canvasToFile(bestCanvas, { mimeType, quality, fileNamePrefix })
  }

  const captureBurstContactSheet = async ({
    frameCount = 4,
    intervalMs = 180,
    mimeType = 'image/jpeg',
    quality = 0.9,
    fileNamePrefix = 'live_contact_sheet'
  } = {}) => {
    const capturedFrames = []

    for (let index = 0; index < frameCount; index += 1) {
      capturedFrames.push(captureFrameCanvas())
      if (index < frameCount - 1) {
        await wait(intervalMs)
      }
    }

    if (!capturedFrames.length) {
      throw new Error('无法从实时画面获取连续帧')
    }

    const columns = 2
    const rows = Math.ceil(capturedFrames.length / columns)
    const maxWidth = Math.max(...capturedFrames.map((canvas) => canvas.width))
    const maxHeight = Math.max(...capturedFrames.map((canvas) => canvas.height))
    const gap = 10

    const sheet = document.createElement('canvas')
    sheet.width = columns * maxWidth + (columns - 1) * gap
    sheet.height = rows * maxHeight + (rows - 1) * gap

    const sheetContext = sheet.getContext('2d')
    sheetContext.fillStyle = '#080808'
    sheetContext.fillRect(0, 0, sheet.width, sheet.height)

    capturedFrames.forEach((canvas, index) => {
      const row = Math.floor(index / columns)
      const column = index % columns
      const startX = column * (maxWidth + gap)
      const startY = row * (maxHeight + gap)
      sheetContext.drawImage(canvas, startX, startY, maxWidth, maxHeight)
    })

    return canvasToFile(sheet, { mimeType, quality, fileNamePrefix })
  }

  const handleDeviceChange = () => {
    refreshCameraDevices(false)
  }

  onMounted(() => {
    if (supportsCameraApi()) {
      refreshCameraDevices(false)
      navigator.mediaDevices?.addEventListener?.('devicechange', handleDeviceChange)
    }
  })

  onBeforeUnmount(() => {
    stopLiveStream()
    navigator.mediaDevices?.removeEventListener?.('devicechange', handleDeviceChange)
  })

  return {
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
    captureLiveFrame,
    captureBestFrame,
    captureBurstContactSheet
  }
}
