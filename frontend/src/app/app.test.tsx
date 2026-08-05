import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '@/modules/auth/presentation/auth-provider'
import { allowedInteractionResource, stubFetch } from '@/test/builders'

import { AppRoutes } from './app-routes'

function renderApp(initialEntry = '/', routes: Record<string, unknown> = {}) {
  window.localStorage.setItem(
    'sentinel.auth.session',
    JSON.stringify({
      accessToken: 'test.jwt.token',
      expiresAt: '2099-08-04T12:00:00Z',
      username: 'sentinel.demo',
    }),
  )
  vi.stubGlobal(
    'fetch',
    stubFetch({ '/api/v1/auth/me': { username: 'sentinel.demo' }, ...routes }),
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
  it('offers the security workspace sections', async () => {
    renderApp()

    const navigation = await screen.findByRole('navigation', { name: 'Navegación principal' })
    const links = Array.from(navigation.querySelectorAll('a')).map((link) => link.textContent)

    expect(links).toEqual([
      'Consultar',
      'Historial',
      'Seguridad',
      'Aprobaciones',
      'Políticas',
      'Laboratorio',
    ])
    expect(screen.queryByRole('link', { name: /dashboard/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /panel/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /conversacion/i })).not.toBeInTheDocument()
  })

  it('navigates from Consultar to Historial', async () => {
    renderApp('/', {
        '/api/v1/interactions': {
          items: [allowedInteractionResource()],
          page: { page: 1, page_size: 10, total: 1 },
        },
      })
    const user = userEvent.setup()

    expect(await screen.findByRole('heading', { name: 'Consultar', level: 1 })).toBeInTheDocument()

    await user.click(screen.getByRole('link', { name: 'Historial' }))

    expect(await screen.findByRole('heading', { name: 'Historial', level: 1 })).toBeInTheDocument()
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
