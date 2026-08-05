import { ArrowUp, FileJson2, Image, Plus, X } from 'lucide-react'
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
} from '@/contexts/analysis-and-decision/domain/secure-query/secure-query-draft'
import { formatFileSize } from '@/shared/lib/format'
import { Alert, AlertDescription } from '@/shared/interfaces/ui/alert'
import { Button } from '@/shared/interfaces/ui/button'
import { Spinner } from '@/shared/interfaces/ui/spinner'
import { Textarea } from '@/shared/interfaces/ui/textarea'
import { cn } from '@/shared/interfaces/utils'

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
  const actionLabel = submitActionLabel(draft)

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
    <div>
      <form
        onSubmit={handleSubmit}
        noValidate
        className="overflow-hidden rounded-[24px] border border-white/[0.035] bg-[#3a3a37] shadow-[0_18px_55px_rgba(0,0,0,0.24)] transition-shadow focus-within:shadow-[0_20px_65px_rgba(0,0,0,0.32)]"
      >
        <label htmlFor={promptId} className="sr-only">
          Consulta
        </label>
        <Textarea
          id={promptId}
          className="min-h-[92px] resize-none border-0 bg-transparent px-6 pt-5 pb-2 text-[17px] leading-7 text-[#f1efe8] shadow-none placeholder:text-[#aaa89f] focus-visible:border-0 focus-visible:ring-0"
          value={draft.prompt}
          onChange={(event) => onPromptChange(event.target.value)}
          placeholder="¿Cómo puedo ayudarte hoy?"
          disabled={isBusy}
          aria-invalid={overLimit}
          rows={3}
        />

        {hasDocument(draft) && draft.document && (
          <div className="mx-4 mb-2 flex max-w-[360px] items-center gap-3 rounded-xl border border-white/[0.08] bg-black/15 px-3 py-2.5">
            <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-white/[0.06] text-[#d8d6ce] [&_svg]:size-[18px]">
              {draft.document.type.startsWith('image/') ? (
                <Image aria-hidden="true" />
              ) : (
                <FileJson2 aria-hidden="true" />
              )}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium text-[#e9e7df]">
                {draft.document.name}
              </span>
              <span className="block text-[11px] text-[#96958d]">
                {formatFileSize(draft.document.size)}
              </span>
            </span>
            <Button
              type="button"
              size="icon-sm"
              variant="ghost"
              className="text-[#aaa89f] hover:bg-white/[0.08] hover:text-white"
              onClick={removeDocument}
              disabled={isBusy}
              aria-label="Quitar archivo"
            >
              <X aria-hidden="true" />
            </Button>
          </div>
        )}

        <div className="flex min-h-16 items-center gap-2 px-4 pb-3">
          <input
            ref={fileInput}
            id="secure-query-document"
            type="file"
            accept={SUPPORTED_DOCUMENT_ACCEPT}
            className="sr-only"
            onChange={handleFile}
            disabled={isBusy}
            aria-invalid={showProblem}
          />
          <Button
            asChild
            variant="ghost"
            size="icon-lg"
            className="size-10 rounded-full border border-white/[0.18] text-[#eceae3] hover:bg-white/[0.08] hover:text-white"
          >
            <label htmlFor="secure-query-document" title="Adjuntar JSON, PNG o JPEG">
              <Plus className="size-5" aria-hidden="true" />
              <span className="sr-only">Adjuntar archivo</span>
            </label>
          </Button>

          <span
            className={cn(
              'ml-1 hidden text-[11px] tabular-nums text-[#85847d] sm:inline',
              overLimit && 'text-[#ef8f75]',
            )}
            data-testid="prompt-counter"
          >
            {draft.prompt.trim().length.toLocaleString('es')} /{' '}
            {PROMPT_MAX_LENGTH.toLocaleString('es')} caracteres
          </span>

          <div className="ml-auto flex items-center gap-3">
            <span className="hidden text-sm font-medium text-[#f4f2eb] sm:inline">
              Sentinel local
              <span className="ml-2 font-normal text-[#aaa89f]">Seguro</span>
            </span>
            <Button
              type="submit"
              size="icon-lg"
              className="size-10 rounded-full bg-[#eceae3] text-[#222220] hover:bg-white disabled:bg-[#65645f] disabled:text-[#97968f]"
              disabled={isBusy || !canSubmit(draft)}
              aria-label={actionLabel}
              title={actionLabel}
            >
              {isBusy ? <Spinner className="size-4" /> : <ArrowUp className="size-5" />}
            </Button>
          </div>
        </div>
      </form>

      <span className="mt-2 block text-center text-[11px] text-[#77766f] sm:hidden" data-testid="prompt-counter-mobile">
        {draft.prompt.trim().length.toLocaleString('es')} /{' '}
        {PROMPT_MAX_LENGTH.toLocaleString('es')} caracteres
      </span>

      {showProblem && problem && (
        <Alert
          variant="destructive"
          role="alert"
          className="mt-3 border-[#8e4e42]/50 bg-[#3a2420] text-[#ffd8cf]"
        >
          <AlertDescription>{draftProblemMessage(problem)}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}
