import { useId, useRef, type ChangeEvent, type FormEvent } from 'react'

import {
  PROMPT_MAX_LENGTH,
  SUPPORTED_DOCUMENT_ACCEPT,
  canSubmit,
  draftProblem,
  draftProblemMessage,
  hasDocument,
  submitActionLabel,
  type SecureQueryDraft,
} from '@/modules/secure-query/domain/secure-query-draft'
import { formatFileSize } from '@/shared/lib/format'

interface SecureQueryFormProps {
  readonly draft: SecureQueryDraft
  readonly isBusy: boolean
  readonly onPromptChange: (prompt: string) => void
  readonly onDocumentChange: (document: File | null) => void
  readonly onSubmit: () => void
}

export function SecureQueryForm({
  draft,
  isBusy,
  onPromptChange,
  onDocumentChange,
  onSubmit,
}: SecureQueryFormProps) {
  const promptId = useId()
  const fileInput = useRef<HTMLInputElement>(null)
  const problem = draftProblem(draft)
  const showProblem = problem !== null && problem !== 'empty'
  const overLimit = draft.prompt.trim().length > PROMPT_MAX_LENGTH

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (!isBusy && canSubmit(draft)) onSubmit()
  }

  const handleFile = (event: ChangeEvent<HTMLInputElement>) => {
    onDocumentChange(event.target.files?.[0] ?? null)
  }

  const removeDocument = () => {
    onDocumentChange(null)
    if (fileInput.current) fileInput.current.value = ''
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="field">
        <label className="field__label" htmlFor={promptId}>
          Consulta
        </label>
        <textarea
          id={promptId}
          className="field__textarea"
          value={draft.prompt}
          onChange={(event) => onPromptChange(event.target.value)}
          placeholder="Escribe lo que necesitas preguntar al asistente local."
          disabled={isBusy}
        />
        <span
          className={`field__counter${overLimit ? ' field__counter--over' : ''}`}
          data-testid="prompt-counter"
        >
          {draft.prompt.trim().length.toLocaleString('es')} / {PROMPT_MAX_LENGTH.toLocaleString('es')} caracteres
        </span>
      </div>

      <div className="attachment">
        <input
          ref={fileInput}
          id="secure-query-document"
          type="file"
          accept={SUPPORTED_DOCUMENT_ACCEPT}
          className="visually-hidden"
          onChange={handleFile}
          disabled={isBusy}
        />
        {hasDocument(draft) && draft.document ? (
          <div className="attachment__file">
            <span className="attachment__name">{draft.document.name}</span>
            <span className="attachment__size">{formatFileSize(draft.document.size)}</span>
            <button
              type="button"
              className="attachment__remove"
              onClick={removeDocument}
              disabled={isBusy}
            >
              Quitar archivo
            </button>
          </div>
        ) : (
          <label className="attachment__button" htmlFor="secure-query-document">
            Adjuntar archivo (opcional)
          </label>
        )}
        <p className="field__hint">
          JSON, PDF, Word, Excel, PNG o JPEG de hasta 5 MB. La IA local valida el contenido antes
          de que el asistente pueda usarlo.
        </p>
      </div>

      {showProblem && (
        <p className="notice notice--error" role="alert">
          {draftProblemMessage(problem)}
        </p>
      )}

      <div className="form-actions">
        <button type="submit" className="button button--primary" disabled={isBusy || !canSubmit(draft)}>
          {submitActionLabel(draft)}
        </button>
      </div>
    </form>
  )
}
