import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from './api-error'
import { request } from './http-client'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('http client', () => {
  it('returns the parsed payload on success', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify({ ok: true }), { status: 200 })),
    )

    await expect(request<{ ok: boolean }>('/api/v1/health')).resolves.toEqual({ ok: true })
  })

  it('reports an unreachable backend in plain language', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )

    await expect(request('/api/v1/health')).rejects.toMatchObject({
      kind: 'offline',
      message: expect.stringContaining('No pudimos conectar'),
    })
  })

  it('never surfaces a stack trace or an internal path', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({ detail: 'Traceback (most recent call last): File "app/main.py"' }),
            { status: 500 },
          ),
      ),
    )

    const error = await request('/api/v1/secure-queries').catch((caught: unknown) => caught)

    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).message).not.toContain('Traceback')
    expect((error as ApiError).message).not.toContain('app/main.py')
  })

  it('keeps a short human message coming from the backend', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          new Response(JSON.stringify({ detail: 'Se necesita al menos una consulta o un documento.' }), {
            status: 400,
          }),
      ),
    )

    await expect(request('/api/v1/secure-queries')).rejects.toMatchObject({
      message: 'Se necesita al menos una consulta o un documento.',
    })
  })

  it('marks a timeout as retryable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new DOMException('timeout', 'TimeoutError')
      }),
    )

    const error = await request('/api/v1/interactions').catch((caught: unknown) => caught)
    expect((error as ApiError).kind).toBe('timeout')
    expect((error as ApiError).isRetryable).toBe(true)
  })
})
