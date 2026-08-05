import { describe, expect, it } from 'vitest'

import {
  PROMPT_MAX_LENGTH,
  canSubmit,
  draftProblem,
  emptyDraft,
  submitActionLabel,
} from './secure-query-draft'

function testFile(name = 'inventario.json', type = 'application/json', size = 1024): File {
  const file = new File(['{}'], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

describe('SecureQueryDraft', () => {
  it('needs at least a prompt or a document', () => {
    expect(draftProblem(emptyDraft())).toBe('empty')
    expect(canSubmit(emptyDraft())).toBe(false)
  })

  it('accepts a prompt alone', () => {
    expect(canSubmit({ prompt: 'Explícame DDD', document: null })).toBe(true)
  })

  it('accepts a document alone', () => {
    expect(canSubmit({ prompt: '   ', document: testFile() })).toBe(true)
  })

  it('accepts a prompt with a document', () => {
    expect(canSubmit({ prompt: 'Resume esto', document: testFile() })).toBe(true)
  })

  it('rejects a prompt over the length limit', () => {
    const draft = { prompt: 'a'.repeat(PROMPT_MAX_LENGTH + 1), document: null }
    expect(draftProblem(draft)).toBe('prompt_too_long')
  })

  it('rejects a document over five megabytes', () => {
    const draft = { prompt: '', document: testFile('grande.json', 'application/json', 6 * 1024 * 1024) }
    expect(draftProblem(draft)).toBe('document_too_large')
  })

  it('accepts JSON and image MIME types', () => {
    for (const file of [
      testFile('datos.json', 'application/json'),
      testFile('captura.png', 'image/png'),
      testFile('foto.jpg', 'image/jpeg'),
    ]) {
      expect(draftProblem({ prompt: '', document: file })).toBeNull()
    }
  })

  it('rejects a document with an unsupported format', () => {
    const draft = { prompt: '', document: testFile('archivo.zip', 'application/zip') }
    expect(draftProblem(draft)).toBe('document_unsupported')
  })

  it('accepts a .json file even when the browser reports no MIME type', () => {
    const draft = { prompt: '', document: testFile('inventario.json', '') }
    expect(draftProblem(draft)).toBeNull()
  })

  it('accepts a known extension when the browser reports no MIME type', () => {
    expect(draftProblem({ prompt: '', document: testFile('captura.png', '') })).toBeNull()
  })

  it('promises an answer only when there is a question', () => {
    expect(submitActionLabel({ prompt: 'Hola', document: null })).toBe('Analizar y consultar')
    expect(submitActionLabel({ prompt: '', document: testFile() })).toBe('Analizar documento')
  })
})
