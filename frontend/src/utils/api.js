<<<<<<< HEAD
﻿const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export const API_BASE_URL = configuredBaseUrl.replace(/\/$/, '')
export const WS_BASE_URL = API_BASE_URL.replace(/^http/i, 'ws')

export const buildApiUrl = (path) => `${API_BASE_URL}${path}`
export const buildWsUrl = (path) => `${WS_BASE_URL}${path}`
=======
const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://101.33.210.169:6063'

export const API_BASE_URL = configuredBaseUrl.replace(/\/$/, '')

export const buildApiUrl = (path) => `${API_BASE_URL}${path}`
>>>>>>> origin/main

export const readApiPayload = async (response) => {
  const rawText = await response.text()
  if (!rawText) {
    return {}
  }

  try {
    return JSON.parse(rawText)
  } catch {
    return { detail: rawText }
  }
}
<<<<<<< HEAD

const mapLegacyModeToV2 = (legacyMode) => {
  if (legacyMode === 'SHOOTING_POSTURE' || legacyMode === 'SHOOTING_WEAPON') return 'shooting_posture'
  if (legacyMode === 'SHOOTING_TARGET' || legacyMode === 'SHOOTING_FLOW') return 'shooting_flow'
  if (legacyMode === 'COMBAT_FIGHT') return 'combat_action'
  return 'combat_full'
}

export const analyzeWithV2 = async ({ file, legacyMode }) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('mode', mapLegacyModeToV2(legacyMode))

  const response = await fetch(buildApiUrl('/api/v2/analyze/file'), {
    method: 'POST',
    body: formData
  })

  const data = await readApiPayload(response)
  return { ok: response.ok, data }
}

export const analyzeWithV1Fallback = async ({ file, legacyMode }) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('mode', legacyMode)

  const response = await fetch(buildApiUrl('/api/analyze-vision'), {
    method: 'POST',
    body: formData
  })

  const data = await readApiPayload(response)
  return { ok: response.ok, data }
}

=======
>>>>>>> origin/main
