export const CONTENT_TYPES = ['prompt', 'document', 'prompt_with_document'] as const

export type ContentType = (typeof CONTENT_TYPES)[number]

const CONTENT_TYPE_LABELS: Record<ContentType, string> = {
  prompt: 'Consulta',
  document: 'Documento',
  prompt_with_document: 'Consulta con documento',
}

export function isContentType(value: unknown): value is ContentType {
  return typeof value === 'string' && (CONTENT_TYPES as readonly string[]).includes(value)
}

export function contentTypeLabel(contentType: ContentType): string {
  return CONTENT_TYPE_LABELS[contentType]
}

export function includesDocument(contentType: ContentType): boolean {
  return contentType !== 'prompt'
}

export function includesPrompt(contentType: ContentType): boolean {
  return contentType !== 'document'
}
