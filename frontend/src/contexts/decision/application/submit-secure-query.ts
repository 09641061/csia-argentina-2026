import type { DecisionRepository, SecureQueryDraft } from '@/contexts/decision/domain/decision-repository'

const MAX_FILE_SIZE = 10 * 1024 * 1024
const ACCEPTED_TYPES = new Set(['application/json', 'image/png', 'image/jpeg'])

export class SubmitSecureQuery {
  private readonly repository: DecisionRepository
  constructor(repository: DecisionRepository) { this.repository = repository }

  execute(draft: SecureQueryDraft, signal?: AbortSignal) {
    if (!draft.prompt.trim() && !draft.file) throw new Error('Escribe una consulta o adjunta un archivo.')
    if (draft.prompt.trim().length > 8_000) throw new Error('La consulta no puede superar 8.000 caracteres.')
    if (draft.file && draft.file.size > MAX_FILE_SIZE) throw new Error('El archivo no puede superar 10 MB.')
    if (draft.file && !ACCEPTED_TYPES.has(draft.file.type)) throw new Error('Sólo se admiten archivos JSON, PNG y JPEG.')
    return this.repository.submit({ prompt: draft.prompt.trim(), file: draft.file }, signal)
  }
}
