const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://101.33.210.169:6063'

export const API_BASE_URL = configuredBaseUrl.replace(/\/$/, '')

export const buildApiUrl = (path) => `${API_BASE_URL}${path}`

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
