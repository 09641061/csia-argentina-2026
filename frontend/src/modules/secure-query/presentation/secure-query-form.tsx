import { ArrowRight, FileJson2, Image, Paperclip, Sparkles, X } from 'lucide-react'
import { useId, useRef, type ChangeEvent, type FormEvent } from 'react'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
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

const QUICK_PROMPTS = ['Resumí este documento', 'Detectá información sensible', 'Explicá los puntos principales']

interface SecureQueryFormProps {
  readonly draft: SecureQueryDraft
  readonly isBusy: boolean
  readonly onPromptChange: (prompt: string) => void
  readonly onDocumentChange: (document: File | null) => void
  readonly onSubmit: () => void
}

export function SecureQueryForm({ draft, isBusy, onPromptChange, onDocumentChange, onSubmit }: SecureQueryFormProps) {
  const promptId = useId()
  const fileInput = useRef<HTMLInputElement>(null)
  const problem = draftProblem(draft)
  const showProblem = problem !== null && problem !== 'empty'
  const overLimit = draft.prompt.trim().length > PROMPT_MAX_LENGTH

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (!isBusy && canSubmit(draft)) onSubmit()
  }
  const handleFile = (event: ChangeEvent<HTMLInputElement>) => onDocumentChange(event.target.files?.[0] ?? null)
  const removeDocument = () => {
    onDocumentChange(null)
    if (fileInput.current) fileInput.current.value = ''
  }

  return (
    <form className="flex h-full flex-col" onSubmit={handleSubmit} noValidate>
      <div className="flex-1 space-y-6 p-5 sm:p-7">
        <div>
          <div className="mb-3 flex items-center justify-between gap-4">
            <label className="text-sm font-semibold" htmlFor={promptId}>¿Qué querés consultar?</label>
            <span className={cn('text-xs tabular-nums text-muted-foreground', overLimit && 'text-destructive')} data-testid="prompt-counter">
              {draft.prompt.trim().length.toLocaleString('es')} / {PROMPT_MAX_LENGTH.toLocaleString('es')} caracteres
            </span>
          </div>
          <Textarea
            id={promptId}
            aria-label="Consulta"
            className="min-h-48 resize-y rounded-xl border-border/80 bg-background/40 px-4 py-4 text-base leading-7 shadow-none focus-visible:border-primary"
            value={draft.prompt}
            onChange={(event) => onPromptChange(event.target.value)}
            placeholder="Escribí tu consulta acá. Sentinel la revisará antes de procesarla…"
            disabled={isBusy}
            aria-invalid={overLimit}
          />
          {!draft.prompt && !isBusy && (
            <div className="mt-3 flex flex-wrap items-center gap-2" aria-label="Consultas sugeridas">
              <span className="mr-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">Sugerencias</span>
              {QUICK_PROMPTS.map((prompt) => (
                <button className="rounded-full border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/60 hover:bg-primary/10 hover:text-foreground" type="button" key={prompt} onClick={() => onPromptChange(prompt)}>
                  {prompt}
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          <input ref={fileInput} id="secure-query-document" type="file" accept={SUPPORTED_DOCUMENT_ACCEPT} className="sr-only" onChange={handleFile} disabled={isBusy} aria-invalid={showProblem} />
          {hasDocument(draft) && draft.document ? (
            <div className="flex items-center gap-3 rounded-xl border border-primary/30 bg-primary/5 p-4">
              <span className="grid size-11 shrink-0 place-items-center rounded-lg bg-primary/15 text-primary [&_svg]:size-5">
                {draft.document.type.startsWith('image/') ? <Image aria-hidden="true" /> : <FileJson2 aria-hidden="true" />}
              </span>
              <span className="min-w-0 flex-1"><span className="block truncate text-sm font-medium">{draft.document.name}</span><span className="block text-xs text-muted-foreground">{formatFileSize(draft.document.size)}</span></span>
              <Button type="button" size="icon" variant="ghost" onClick={removeDocument} disabled={isBusy} aria-label="Quitar archivo"><X aria-hidden="true" /></Button>
            </div>
          ) : (
            <Button asChild variant="outline" className="h-auto w-full justify-start rounded-xl border-dashed bg-background/30 px-4 py-5 shadow-none hover:border-primary/50 hover:bg-primary/5">
              <label htmlFor="secure-query-document"><span className="mr-2 grid size-9 place-items-center rounded-lg bg-primary/10 text-primary"><Paperclip aria-hidden="true" /></span><span className="text-left"><span className="block font-medium">Adjuntar archivo</span><span className="block text-xs font-normal text-muted-foreground">JSON, PNG o JPEG · máximo 5 MB</span></span></label>
            </Button>
          )}
          <p className="mt-2 text-xs text-muted-foreground">El contenido se valida dentro del perímetro Sentinel.</p>
        </div>

        {showProblem && problem && <Alert variant="destructive" role="alert"><AlertDescription>{draftProblemMessage(problem)}</AlertDescription></Alert>}
      </div>
      <div className="flex items-center justify-between gap-4 border-t bg-muted/20 px-5 py-4 sm:px-7">
        <span className="hidden items-center gap-2 text-xs text-muted-foreground sm:flex"><span className="size-1.5 rounded-full bg-emerald-400" /> Canal protegido</span>
        <Button className="ml-auto rounded-lg" type="submit" size="lg" disabled={isBusy || !canSubmit(draft)}>
          {isBusy ? <Spinner data-icon="inline-start" /> : <Sparkles data-icon="inline-start" aria-hidden="true" />}
          {isBusy ? 'Procesando…' : submitActionLabel(draft)}
          {!isBusy && <ArrowRight aria-hidden="true" />}
        </Button>
      </div>
    </form>
  )
}
