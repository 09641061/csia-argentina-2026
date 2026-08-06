import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AppRoutes } from '@/app/app-routes'
import { AuthProvider } from '@/contexts/iam/interfaces/auth-provider'

function renderAuthFlow(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </MemoryRouter>,
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
  window.localStorage.clear()
})

describe('Autenticación', () => {
  it('redirects a visitor to login before rendering protected content', async () => {
    renderAuthFlow('/')

    expect(await screen.findByRole('heading', { name: 'Iniciar sesión' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /¿En qué puedo ayudarte/i })).not.toBeInTheDocument()
  })

  it('registers a user, stores the JWT session and opens the protected portal', async () => {
    const fetchStub = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = input.toString()
      if (url.includes('/api/v1/auth/register')) {
        return new Response(
          JSON.stringify({
            access_token: 'header.payload.signature',
            token_type: 'bearer',
            expires_at: '2099-08-04T12:00:00Z',
            username: 'sentinel.demo',
          }),
          { status: 201, headers: { 'Content-Type': 'application/json' } },
        )
      }
      if (url.includes('/api/v1/auth/me')) {
        const headers = new Headers(init?.headers)
        expect(headers.get('Authorization')).toBe('Bearer header.payload.signature')
        return new Response(JSON.stringify({ username: 'sentinel.demo' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      if (url.includes('/api/v1/chat/conversations')) {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      if (url.includes('/api/v1/health')) {
        return new Response(JSON.stringify({
          status: 'ok', database: true,
          security_model_available: true, discovery_model_available: true,
          generation_model_available: true, vision_model_available: true,
          security_model: 'local', discovery_model: 'local', generation_model: 'local', vision_model: 'local',
        }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      }
      return new Response(JSON.stringify({ detail: 'Not found' }), { status: 404 })
    })
    vi.stubGlobal('fetch', fetchStub)
    const user = userEvent.setup()
    renderAuthFlow('/register')

    await user.type(screen.getByLabelText('Usuario'), 'Sentinel.Demo')
    await user.type(screen.getByLabelText('Contraseña'), 'DemoSecure2026')
    await user.type(screen.getByLabelText('Confirmar contraseña'), 'DemoSecure2026')
    await user.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    expect(await screen.findByRole('heading', { name: /¿En qué puedo ayudarte, sentinel/i })).toBeInTheDocument()
    expect(fetchStub).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/auth/register'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(window.localStorage.getItem('sentinel.auth.session')).toContain(
      'header.payload.signature',
    )
  })

  it('shows a useful message when login credentials are rejected', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: 'Usuario o contraseña incorrectos.' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )
    const user = userEvent.setup()
    renderAuthFlow('/login')

    await user.type(screen.getByLabelText('Usuario'), 'sentinel.demo')
    await user.type(screen.getByLabelText('Contraseña'), 'WrongPass2026')
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Usuario o contraseña incorrectos.')
  })
})
