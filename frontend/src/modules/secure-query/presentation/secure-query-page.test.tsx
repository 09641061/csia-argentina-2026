import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  allowedInteractionResource,
  blockedInteractionResource,
  secureQueryResponse,
  stubFetch,
} from '@/test/builders'

import { SecureQueryPage } from './secure-query-page'

function renderPage() {
  return render(
    <MemoryRouter>
      <SecureQueryPage />
    </MemoryRouter>,
  )
}

function jsonFile(name = 'inventario.json', type = 'application/json'): File {
  return new File([JSON.stringify({ services: [] })], name, { type })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Consultar', () => {
  it('sends a prompt without a document and shows the generated answer', async () => {
    const fetchStub = stubFetch({
      '/api/v1/secure-queries': secureQueryResponse(
        allowedInteractionResource(),
        'Una arquitectura orientada a eventos desacopla los servicios.',
      ),
    })
    vi.stubGlobal('fetch', fetchStub)
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Consulta'), 'Explícame la arquitectura de eventos')
    await user.click(screen.getByRole('button', { name: 'Analizar y consultar' }))

    expect(await screen.findByText('Consulta permitida')).toBeInTheDocument()
    expect(
      screen.getByText('Una arquitectura orientada a eventos desacopla los servicios.'),
    ).toBeInTheDocument()
    expect(screen.getByText(/Riesgo bajo/)).toBeInTheDocument()

    const body = fetchStub.mock.calls[0][1]?.body as FormData
    expect(body.get('prompt')).toBe('Explícame la arquitectura de eventos')
    expect(body.get('file')).toBeNull()
  })

  it('shows a blocked result with masked findings and no answer', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch({ '/api/v1/secure-queries': secureQueryResponse(blockedInteractionResource(), null) }),
    )
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Consulta'), 'La contraseña es SuperSecret123')
    await user.click(screen.getByRole('button', { name: 'Analizar y consultar' }))

    expect(await screen.findByText('Consulta bloqueada')).toBeInTheDocument()
    expect(screen.getByText('La consulta contiene información sensible.')).toBeInTheDocument()
    expect(
      screen.getByText('El contenido no se envió al generador de respuestas de la IA.'),
    ).toBeInTheDocument()
    // "Contraseña" appears twice on purpose: once as the kind of information
    // detected and once in the masked finding itself.
    expect(screen.getAllByText('Contraseña').length).toBeGreaterThan(0)
    expect(screen.getByText('Sup*********23')).toBeInTheDocument()
    expect(screen.getByText(/Riesgo alto/)).toBeInTheDocument()
    expect(screen.queryByText(/Respuesta del asistente local/)).not.toBeInTheDocument()
  })

  it('never offers a sanitized version of the blocked content', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch({ '/api/v1/secure-queries': secureQueryResponse(blockedInteractionResource(), null) }),
    )
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Consulta'), 'La contraseña es SuperSecret123')
    await user.click(screen.getByRole('button', { name: 'Analizar y consultar' }))
    await screen.findByText('Consulta bloqueada')

    expect(screen.queryByText(/versión segura/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/sanitiz/i)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /copiar/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /descargar/i })).not.toBeInTheDocument()
  })

  it('sends the attached document and labels the action as a document review', async () => {
    const fetchStub = stubFetch({
      '/api/v1/secure-queries': secureQueryResponse(
        allowedInteractionResource({ content_type: 'document', generation_status: 'not_requested' }),
        null,
      ),
    })
    vi.stubGlobal('fetch', fetchStub)
    const user = userEvent.setup()
    renderPage()

    await user.upload(screen.getByLabelText(/Adjuntar archivo/), jsonFile())
    expect(screen.getByText('inventario.json')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Analizar documento' }))

    expect(await screen.findByText('Documento permitido')).toBeInTheDocument()
    expect(screen.getByText(/no se generó una respuesta/)).toBeInTheDocument()
    const body = fetchStub.mock.calls[0][1]?.body as FormData
    expect((body.get('file') as File).name).toBe('inventario.json')
  })

  it('lets the user remove the attached file before sending', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.upload(screen.getByLabelText(/Adjuntar archivo/), jsonFile())
    expect(screen.getByText('inventario.json')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Quitar archivo' }))

    expect(screen.queryByText('inventario.json')).not.toBeInTheDocument()
    // With nothing left to send, the action goes back to its document wording
    // and stays disabled.
    expect(screen.getByRole('button', { name: 'Analizar documento' })).toBeDisabled()
  })

  it('accepts supported files and rejects unknown formats at the file picker', async () => {
    const fetchStub = stubFetch({})
    vi.stubGlobal('fetch', fetchStub)
    const user = userEvent.setup()
    renderPage()

    const input = screen.getByLabelText(/Adjuntar archivo/) as HTMLInputElement
    expect(input.accept).toContain('application/pdf')
    expect(input.accept).toContain('.docx')
    expect(input.accept).toContain('image/png')

    await user.upload(input, new File(['%PDF-1.4'], 'informe.pdf', { type: 'application/pdf' }))

    expect(input.files).toHaveLength(1)
    expect(screen.getByText('informe.pdf')).toBeInTheDocument()

    await user.upload(input, new File(['zip'], 'archivo.zip', { type: 'application/zip' }))

    expect(input.files).toHaveLength(0)
    expect(screen.queryByText('archivo.zip')).not.toBeInTheDocument()
    expect(fetchStub).not.toHaveBeenCalled()
  })

  it('keeps the submit button disabled while nothing was written or attached', () => {
    renderPage()
    expect(screen.getByRole('button', { name: 'Analizar documento' })).toBeDisabled()
  })

  it('shows the analysis progress state while the review runs', async () => {
    let release: (value: Response) => void = () => {}
    vi.stubGlobal(
      'fetch',
      vi.fn(
        () =>
          new Promise<Response>((resolve) => {
            release = resolve
          }),
      ),
    )
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Consulta'), 'Una consulta cualquiera')
    await user.click(screen.getByRole('button', { name: 'Analizar y consultar' }))

    expect(await screen.findByText('Analizando el contenido…')).toBeInTheDocument()

    release(
      new Response(JSON.stringify(secureQueryResponse(allowedInteractionResource())), {
        status: 200,
      }),
    )
    await waitFor(() => expect(screen.getByText('Consulta permitida')).toBeInTheDocument())
  })

  it('explains that the content passed the review when the generation failed', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch({
        '/api/v1/secure-queries': secureQueryResponse(
          allowedInteractionResource({
            generation_status: 'failed',
            generation_error: 'El asistente local no respondió dentro del tiempo configurado.',
            generated_at: null,
          }),
          null,
        ),
      }),
    )
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Consulta'), 'Una consulta cualquiera')
    await user.click(screen.getByRole('button', { name: 'Analizar y consultar' }))

    expect(
      await screen.findByText(
        /El contenido superó la revisión, pero no fue posible generar la respuesta\./,
      ),
    ).toBeInTheDocument()
  })

  it('offers a retry when the backend is unreachable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Consulta'), 'Una consulta cualquiera')
    await user.click(screen.getByRole('button', { name: 'Analizar y consultar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/No pudimos conectar/)
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
  })

  it('shows no chat interface: there is a single result, not a message list', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch({ '/api/v1/secure-queries': secureQueryResponse(allowedInteractionResource()) }),
    )
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Consulta'), 'Primera consulta')
    await user.click(screen.getByRole('button', { name: 'Analizar y consultar' }))
    await screen.findByText('Consulta permitida')

    expect(screen.getAllByTestId('secure-query-result')).toHaveLength(1)

    await user.click(screen.getByRole('button', { name: 'Realizar una nueva consulta' }))
    expect(screen.queryByTestId('secure-query-result')).not.toBeInTheDocument()
    expect(screen.getByLabelText('Consulta')).toHaveValue('')
  })

  it('counts characters as the user types', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Consulta'), 'Hola')

    // The thousands separator depends on the ICU data of the runtime, so the
    // assertion checks the counted value rather than its formatting.
    expect(screen.getByTestId('prompt-counter')).toHaveTextContent(/^4 \/ 8[.,]?000 caracteres$/)
  })
})
