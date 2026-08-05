import { useMemo } from 'react'

import { HttpSecureQueryRepository } from '@/contexts/analysis-and-decision/infrastructure/secure-query/http-secure-query-repository'
import { useOptionalAuth } from '@/contexts/iam/interfaces/auth-context'
import { ClaudeSpark } from '@/shared/interfaces/components/claude-brand'
import { ErrorNotice } from '@/shared/interfaces/components/error-notice'
import { LoadingStatus } from '@/shared/interfaces/components/loading-status'
import { cn } from '@/shared/interfaces/utils'

import { SecureQueryForm } from './secure-query-form'
import { SecureQueryResult } from './secure-query-result'
import { useSecureQuery } from './use-secure-query'

export function SecureQueryPage() {
  const repository = useMemo(() => new HttpSecureQueryRepository(), [])
  const auth = useOptionalAuth()
  const { state, setPrompt, setDocument, submit, reset } = useSecureQuery(repository)
  const isBusy = state.phase === 'analyzing' || state.phase === 'generating'
  const hasResult = state.phase === 'done' || state.phase === 'error'
  const greeting = auth?.session?.username
    ? `¡${auth.session.username} ha vuelto!`
    : '¿Qué quieres consultar?'

  return (
    <div className="min-h-full px-4 sm:px-7 lg:px-10">
      <section
        className={cn(
          'mx-auto flex w-full max-w-[842px] flex-col pb-16 transition-[padding] duration-300',
          hasResult ? 'pt-24' : 'min-h-svh justify-center pt-20 md:-translate-y-8',
        )}
      >
        <header className="mb-10 flex items-center justify-center gap-4 text-center">
          <ClaudeSpark className="size-10 shrink-0 sm:size-11" />
          <h1 className="font-serif text-[32px] font-normal tracking-[-0.025em] text-[#c9c7bf] sm:text-[42px]">
            <span className="sr-only">Consultar</span>
            <span aria-hidden="true">{greeting}</span>
          </h1>
        </header>

        <SecureQueryForm
          draft={state.draft}
          isBusy={isBusy}
          onPromptChange={setPrompt}
          onDocumentChange={setDocument}
          onSubmit={submit}
        />

        <p className="mt-3 text-center text-[11px] leading-5 text-[#77766f]">
          Sentinel puede cometer errores. El contenido se revisa localmente antes de generar.
        </p>

        <div className="mt-6">
          {state.phase === 'analyzing' && (
            <LoadingStatus message="Analizando el contenido con IA local…" />
          )}
          {state.phase === 'generating' && (
            <LoadingStatus message="Contenido permitido. Generando la respuesta…" />
          )}
          {state.phase === 'error' && state.errorMessage && (
            <ErrorNotice message={state.errorMessage} onRetry={submit} />
          )}
          {state.phase === 'done' && state.interaction && (
            <SecureQueryResult
              interaction={state.interaction}
              answer={state.answer}
              onNewQuery={reset}
            />
          )}
        </div>
      </section>
    </div>
  )
}
