import { apiBaseUrl, requestTimeoutMs } from '@/shared/infrastructure/config/env'
import {
  clearAuthSession,
  currentAccessToken,
  notifyAuthChanged,
} from '@/contexts/iam/infrastructure/auth-storage'

import { ApiError } from './api-error'

interface RequestOptions {
  readonly method?: 'GET' | 'POST'
  readonly body?: FormData | Record<string, unknown>
  readonly signal?: AbortSignal
  readonly timeoutMs?: number
  readonly authenticated?: boolean
}

const SAFE_MESSAGES: Record<number, string> = {
  400: 'La solicitud no es válida.',
  401: 'Tu sesión no es válida o ha expirado. Vuelve a iniciar sesión.',
  404: 'No encontramos lo que buscabas.',
  413: 'El documento supera el tamaño permitido.',
  415: 'Solo se admiten archivos JSON, PNG y JPEG.',
  422: 'La solicitud no es válida.',
  500: 'El servicio tuvo un problema interno. Vuelve a intentarlo.',
  502: 'El asistente local no está disponible en este momento.',
  503: 'El servicio no está disponible en este momento.',
  504: 'La operación tardó demasiado. Vuelve a intentarlo.',
}

/**
 * Single entry point to the backend.
 *
 * Every network outcome becomes an ApiError with a message written for a
 * person. A caller never sees a status code, a URL or a raw response body, so
 * no internal detail can leak into the interface by accident.
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const {
    method = 'GET',
    body,
    signal,
    timeoutMs = requestTimeoutMs,
    authenticated = true,
  } = options

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(new DOMException('timeout', 'TimeoutError')), timeoutMs)
  const onAbort = () => controller.abort(signal?.reason)
  signal?.addEventListener('abort', onAbort, { once: true })

  let response: Response
  try {
    const headers = new Headers()
    if (!(body instanceof FormData) && body !== undefined) {
      headers.set('Content-Type', 'application/json')
    }
    if (authenticated) {
      const accessToken = currentAccessToken()
      if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
    }
    response = await fetch(`${apiBaseUrl}${path}`, {
      method,
      signal: controller.signal,
      headers,
      body: body instanceof FormData ? body : body === undefined ? undefined : JSON.stringify(body),
    })
  } catch (error) {
    if (signal?.aborted) throw error
    if (isTimeout(error)) {
      throw new ApiError('timeout', 'La operación tardó demasiado. Vuelve a intentarlo.')
    }
    throw new ApiError(
      'offline',
      'No pudimos conectar con el servicio de Claude. Comprueba que esté en ejecución e inténtalo de nuevo.',
    )
  } finally {
    clearTimeout(timeout)
    signal?.removeEventListener('abort', onAbort)
  }

  if (!response.ok) {
    if (response.status === 401 && authenticated) {
      clearAuthSession()
      notifyAuthChanged()
    }
    throw new ApiError(kindFor(response.status), await safeMessage(response), response.status)
  }

  try {
    return (await response.json()) as T
  } catch {
    throw new ApiError('server', 'El servicio devolvió una respuesta que no pudimos leer.')
  }
}

function isTimeout(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'TimeoutError'
}

function kindFor(status: number): ApiError['kind'] {
  if (status === 401) return 'unauthorized'
  if (status === 404) return 'not_found'
  if (status === 413) return 'too_large'
  if (status === 415) return 'unsupported_media'
  if (status === 504) return 'timeout'
  if (status >= 500) return 'server'
  if (status >= 400) return 'bad_request'
  return 'unknown'
}

/**
 * Use the backend's own message only when it is a short, human sentence.
 *
 * Anything long, or anything shaped like a path or a stack trace, is replaced
 * by a generic message rather than shown to the user.
 */
async function safeMessage(response: Response): Promise<string> {
  const fallback = SAFE_MESSAGES[response.status] ?? 'No pudimos completar la operación.'
  try {
    const payload = (await response.json()) as { detail?: unknown }
    const detail = payload?.detail
    if (typeof detail === 'string' && detail.length > 0 && detail.length <= 200 && isPresentable(detail)) {
      return detail
    }
  } catch {
    return fallback
  }
  return fallback
}

function isPresentable(detail: string): boolean {
  return !/(Traceback|File "|\bapp[./\\]|https?:\/\/|[A-Za-z]:\\|\bError:)/.test(detail)
}
