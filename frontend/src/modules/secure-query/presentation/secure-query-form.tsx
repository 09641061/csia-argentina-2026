import { FileJson2, Image, Send, Upload, X } from 'lucide-react'
import { useId, useRef, type ChangeEvent, type FormEvent } from 'react'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Field, FieldDescription, FieldGroup, FieldLabel } from '@/components/ui/field'
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
    <Card>
      <form onSubmit={handleSubmit} noValidate>
        <CardHeader>
          <CardTitle>Nueva consulta segura</CardTitle>
          <CardDescription>Escribe una consulta, adjunta un archivo o combina ambos.</CardDescription>
        </CardHeader>
        <CardContent>
          <FieldGroup>
            <Field data-invalid={overLimit}>
              <div className="flex items-center justify-between gap-4">
                <FieldLabel htmlFor={promptId}>Consulta</FieldLabel>
                <span
                  className={cn(
                    'text-xs tabular-nums text-muted-foreground',
                    overLimit && 'text-destructive',
                  )}
                  data-testid="prompt-counter"
                >
                  {draft.prompt.trim().length.toLocaleString('es')} /{' '}
                  {PROMPT_MAX_LENGTH.toLocaleString('es')} caracteres
                </span>
              </div>
              <Textarea
                id={promptId}
                className="min-h-36 resize-y"
                value={draft.prompt}
                onChange={(event) => onPromptChange(event.target.value)}
                placeholder="Escribe lo que necesitas consultar al asistente local…"
                disabled={isBusy}
                aria-invalid={overLimit}
              />
            </Field>

            <Field data-invalid={showProblem}>
              <FieldLabel htmlFor="secure-query-document">Documento opcional</FieldLabel>
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

              {hasDocument(draft) && draft.document ? (
                <div className="flex items-center gap-3 rounded-lg border p-3">
                  <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-muted [&_svg]:size-5">
                    {draft.document.type.startsWith('image/') ? (
                      <Image aria-hidden="true" />
                    ) : (
                      <FileJson2 aria-hidden="true" />
                    )}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium">{draft.document.name}</span>
                    <span className="block text-xs text-muted-foreground">
                      {formatFileSize(draft.document.size)}
                    </span>
                  </span>
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    onClick={removeDocument}
                    disabled={isBusy}
                    aria-label="Quitar archivo"
                  >
                    <X aria-hidden="true" />
                  </Button>
                </div>
              ) : (
                <Button asChild variant="outline" className="h-auto w-full justify-start py-4">
                  <label htmlFor="secure-query-document">
                    <Upload data-icon="inline-start" aria-hidden="true" />
                    <span className="text-left">
                      <span className="block font-medium">Adjuntar archivo</span>
                      <span className="block text-xs font-normal text-muted-foreground">
                        JSON, PNG o JPEG
                      </span>
                    </span>
                  </label>
                </Button>
              )}
              <FieldDescription>JSON, PNG o JPEG · Máximo 5 MB.</FieldDescription>
            </Field>

            {showProblem && problem && (
              <Alert variant="destructive" role="alert">
                <AlertDescription>{draftProblemMessage(problem)}</AlertDescription>
              </Alert>
            )}
          </FieldGroup>
        </CardContent>
        <CardFooter className="justify-end">
          <Button type="submit" size="lg" disabled={isBusy || !canSubmit(draft)}>
            {isBusy ? (
              <Spinner data-icon="inline-start" />
            ) : (
              <Send data-icon="inline-start" aria-hidden="true" />
            )}
            {isBusy ? 'Procesando…' : submitActionLabel(draft)}
          </Button>
        </CardFooter>
      </form>
    </Card>
  )
}
