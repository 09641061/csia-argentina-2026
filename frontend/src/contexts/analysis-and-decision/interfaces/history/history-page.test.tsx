import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  allowedInteractionResource,
  analysisResource,
  blockedInteractionResource,
  stubFetch,
} from '@/test/builders'

import { HistoryPage } from './history-page'
import { InteractionDetailPage } from './interaction-detail-page'

function renderHistory(initialEntry = '/historial') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/historial" element={<HistoryPage />} />
        <Route path="/historial/:interactionId" element={<InteractionDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

function page(items: unknown[], total: number, pageNumber = 1) {
  return { items, page: { page: pageNumber, page_size: 10, total } }
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Historial', () => {
  it('lists the audited interactions with their decision and generation status', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch({
        '/api/v1/interactions': page(
          [allowedInteractionResource(), blockedInteractionResource()],
          2,
        ),
      }),
    )
    renderHistory()

    expect(await screen.findByRole('table')).toBeInTheDocument()
    expect(screen.getByText('permitida')).toBeInTheDocument()
    expect(screen.getByText('bloqueada')).toBeInTheDocument()
    expect(screen.getByText('Respuesta generada')).toBeInTheDocument()
    expect(screen.getByText('No se envió al asistente')).toBeInTheDocument()
    expect(screen.getByText('Página 1 de 1')).toBeInTheDocument()
    expect(screen.getByText('2 consultas')).toBeInTheDocument()
  })

  it('shows an empty state when nothing was reviewed yet', async () => {
    vi.stubGlobal('fetch', stubFetch({ '/api/v1/interactions': page([], 0) }))
    renderHistory()

    expect(await screen.findByText('Todavía no hay consultas')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('paginates and disables the buttons at the edges', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch({ '/api/v1/interactions': page([allowedInteractionResource()], 25) }),
    )
    const user = userEvent.setup()
    renderHistory()

    await screen.findByRole('table')
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()

    const next = screen.getByRole('button', { name: 'Siguiente' })
    expect(next).toBeEnabled()
    await user.click(next)

    expect(await screen.findByRole('table')).toBeInTheDocument()
  })

  it('offers a retry when the history cannot be loaded', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )
    renderHistory()

    expect(await screen.findByRole('alert')).toHaveTextContent(/No pudimos conectar/)
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
  })

  it('opens the detail of a blocked interaction and explains it', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch({
        '/api/v1/interactions/2': blockedInteractionResource({ id: 2, prompt_analysis_id: 10 }),
        '/api/v1/analyses/10': analysisResource({
          risk_level: 'high',
          explanation: 'Se detectó una credencial en la consulta.',
          masked_preview: 'La contraseña es Sup*********23',
        }),
      }),
    )
    renderHistory('/historial/2')

    expect(await screen.findByText('Consulta bloqueada')).toBeInTheDocument()
    expect(screen.getByText('La consulta contiene información sensible.')).toBeInTheDocument()
    expect(
      screen.getByText('El contenido no se envió al generador de respuestas de la IA.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Sup*********23')).toBeInTheDocument()
    expect(screen.getByText('Se detectó una credencial en la consulta.')).toBeInTheDocument()
  })

  it('reports a missing interaction without technical detail', async () => {
    vi.stubGlobal('fetch', stubFetch({}))
    renderHistory('/historial/9999')

    expect(await screen.findByRole('alert')).toHaveTextContent('No encontramos lo que buscabas.')
  })

  it('never renders dashboard widgets', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch({ '/api/v1/interactions': page([allowedInteractionResource()], 1) }),
    )
    const { container } = renderHistory()

    await screen.findByRole('table')

    expect(container.querySelector('canvas')).toBeNull()
    expect(container.querySelector('[data-chart]')).toBeNull()
    expect(screen.queryByText(/métricas/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/ranking/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/tendencia/i)).not.toBeInTheDocument()
  })
})
