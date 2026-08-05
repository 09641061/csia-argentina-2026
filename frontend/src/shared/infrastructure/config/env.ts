const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000'

function readApiBaseUrl(): string {
  const configured = import.meta.env?.VITE_API_BASE_URL
  const value = typeof configured === 'string' && configured.trim() ? configured.trim() : DEFAULT_API_BASE_URL
  return value.replace(/\/+$/, '')
}

export const apiBaseUrl = readApiBaseUrl()

/** Requests are aborted well before the browser gives up, so the UI can explain the wait. */
export const requestTimeoutMs = 240_000
