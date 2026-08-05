import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { allowedInteractionResource, stubFetch } from '@/test/builders'

import { AppRoutes } from './app-routes'

function renderApp(initialEntry = '/') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <AppRoutes />
    </MemoryRouter>,
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Navegación', () => {
  it('offers only Consultar and Historial', () => {
    renderApp()

    const navigation = screen.getByRole('navigation', { name: 'Navegación principal' })
    const links = Array.from(navigation.querySelectorAll('a')).map((link) => link.textContent)

    expect(links).toEqual(['Consultar', 'Historial'])
    expect(screen.queryByRole('link', { name: /dashboard/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /panel/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /conversacion/i })).not.toBeInTheDocument()
  })

  it('navigates from Consultar to Historial', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch({
        '/api/v1/interactions': {
          items: [allowedInteractionResource()],
          page: { page: 1, page_size: 10, total: 1 },
        },
      }),
    )
    const user = userEvent.setup()
    renderApp()

    expect(screen.getByRole('heading', { name: 'Consultar', level: 1 })).toBeInTheDocument()

    await user.click(screen.getByRole('link', { name: 'Historial' }))

    expect(await screen.findByRole('heading', { name: 'Historial', level: 1 })).toBeInTheDocument()
  })

  it('shows a friendly page for an unknown route', () => {
    renderApp('/no-existe')
    expect(screen.getByRole('heading', { name: 'Página no encontrada' })).toBeInTheDocument()
  })

  it('uses the system font stack and a fluid main column', () => {
    renderApp()
    const main = document.querySelector('.app__main')
    expect(main).not.toBeNull()
    expect(document.querySelector('.app__header')).not.toBeNull()
  })
})
