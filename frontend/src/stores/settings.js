import { reactive } from 'vue'

const STORAGE_KEY = 'captp_settings_v1'

const defaultState = {
  sourceType: 'camera',
  cameraDeviceId: '',
  rtspUrl: ''
}

const loadState = () => {
  if (typeof window === 'undefined') {
    return { ...defaultState }
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return { ...defaultState }
    }

    const parsed = JSON.parse(raw)
    return {
      ...defaultState,
      ...parsed
    }
  } catch {
    return { ...defaultState }
  }
}

const settings = reactive(loadState())

const persist = () => {
  if (typeof window === 'undefined') {
    return
  }

  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      sourceType: settings.sourceType,
      cameraDeviceId: settings.cameraDeviceId,
      rtspUrl: settings.rtspUrl
    })
  )
}

export const settingsStore = {
  settings,
  setSourceType(value) {
    settings.sourceType = value
    persist()
  },
  setCameraDeviceId(value) {
    settings.cameraDeviceId = value
    persist()
  },
  setRtspUrl(value) {
    settings.rtspUrl = value
    persist()
  }
}