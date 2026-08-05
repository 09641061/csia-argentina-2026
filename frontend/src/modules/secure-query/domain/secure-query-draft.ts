export const PROMPT_MAX_LENGTH = 8000
export const DOCUMENT_MAX_BYTES = 5 * 1024 * 1024
export const SUPPORTED_DOCUMENT_ACCEPT = [
  'application/json',
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'image/png',
  'image/jpeg',
  '.json',
  '.pdf',
  '.docx',
  '.xlsx',
  '.png',
  '.jpg',
  '.jpeg',
].join(',')

const MIME_TYPES = new Set([
  'application/json',
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'image/png',
  'image/jpeg',
  'image/jpg',
])

const EXTENSIONS = ['.json', '.pdf', '.docx', '.xlsx', '.png', '.jpg', '.jpeg']

export type DraftProblem =
  | 'empty'
  | 'prompt_too_long'
  | 'document_too_large'
  | 'document_unsupported'

/**
 * What the person has typed and attached so far.
 *
 * Only the rules the user needs *before* sending live here: is there anything
 * to send, does it fit, is the attachment a supported file. Whether the content is
 * safe is never decided on this side.
 */
export interface SecureQueryDraft {
  readonly prompt: string
  readonly document: File | null
}

export function emptyDraft(): SecureQueryDraft {
  return { prompt: '', document: null }
}

export function hasPrompt(draft: SecureQueryDraft): boolean {
  return draft.prompt.trim().length > 0
}

export function hasDocument(draft: SecureQueryDraft): boolean {
  return draft.document !== null
}

export function draftProblem(draft: SecureQueryDraft): DraftProblem | null {
  if (!hasPrompt(draft) && !hasDocument(draft)) return 'empty'
  if (draft.prompt.trim().length > PROMPT_MAX_LENGTH) return 'prompt_too_long'
  if (draft.document && draft.document.size > DOCUMENT_MAX_BYTES) return 'document_too_large'
  if (draft.document && !looksLikeSupportedDocument(draft.document)) return 'document_unsupported'
  return null
}

export function canSubmit(draft: SecureQueryDraft): boolean {
  return draftProblem(draft) === null
}

/**
 * Label of the primary button.
 *
 * With a question the user gets an answer; with only a document there is
 * nothing to answer, so the button must not promise one.
 */
export function submitActionLabel(draft: SecureQueryDraft): string {
  return hasPrompt(draft) ? 'Analizar y consultar' : 'Analizar documento'
}

export function draftProblemMessage(problem: DraftProblem): string {
  switch (problem) {
    case 'empty':
      return 'Escribe una consulta o adjunta un archivo para analizar.'
    case 'prompt_too_long':
      return `La consulta no puede superar los ${PROMPT_MAX_LENGTH.toLocaleString('es')} caracteres.`
    case 'document_too_large':
      return 'El documento supera los 5 MB permitidos.'
    case 'document_unsupported':
      return 'Solo se admiten JSON, PDF, Word, Excel, PNG y JPEG.'
  }
}

function looksLikeSupportedDocument(file: File): boolean {
  const type = file.type.split(';')[0].trim().toLowerCase()
  if (MIME_TYPES.has(type)) return true
  // Some browsers report an empty or generic type; fall back to the extension.
  if (type === '' || type === 'application/octet-stream' || type === 'text/plain') {
    const name = file.name.toLowerCase()
    return EXTENSIONS.some((extension) => name.endsWith(extension))
  }
  return false
}
