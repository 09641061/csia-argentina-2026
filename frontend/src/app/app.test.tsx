import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '@/contexts/iam/interfaces/auth-provider'
import { stubFetch } from '@/test/builders'

import { AppRoutes } from './app-routes'

function renderApp(initialEntry = '/', routes: Record<string, unknown> = {}) {
  window.localStorage.setItem(
    'claude.auth.session',
    JSON.stringify({
      accessToken: 'test.jwt.token',
      expiresAt: '2099-08-04T12:00:00Z',
      username: 'claude.demo',
    }),
  )
  vi.stubGlobal(
    'fetch',
    stubFetch({
      '/api/v1/auth/me': { username: 'claude.demo' },
      '/api/v1/chat/conversations': [],
      '/api/v1/health': {
        status: 'ok', database: true,
        security_model_available: true, discovery_model_available: true,
        generation_model_available: true, vision_model_available: true,
        security_model: 'local', discovery_model: 'local', generation_model: 'local', vision_model: 'local',
      },
      ...routes,
    }),
  )
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

describe('Navegación', () => {
  it('offers every frontend bounded context from the Claude-style sidebar', async () => {
    renderApp()

    const navigation = await screen.findByRole('navigation', { name: 'Navegación principal' })
    const links = Array.from(navigation.querySelectorAll('a')).map((link) => link.textContent)

    expect(links).toEqual(['Nuevo chat', 'Chats', 'Análisis'])
    expect(screen.queryByRole('link', { name: /dashboard/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /panel/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /conversacion/i })).not.toBeInTheDocument()
  })

  it('shows a friendly page for an unknown route', async () => {
    renderApp('/no-existe')
    expect(await screen.findByRole('heading', { name: 'Página no encontrada' })).toBeInTheDocument()
  })

  it('uses the shadcn application shell and a fluid main column', async () => {
    renderApp()
    expect((await screen.findAllByRole('banner')).length).toBeGreaterThan(0)
    expect(screen.getByRole('main')).toBeInTheDocument()
  })
})
