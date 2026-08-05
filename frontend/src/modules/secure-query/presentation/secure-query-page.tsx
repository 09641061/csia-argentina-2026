import { useMemo } from 'react'

import { HttpSecureQueryRepository } from '@/modules/secure-query/infrastructure/http-secure-query-repository'
import { ErrorNotice } from '@/shared/ui/error-notice'
import { LoadingStatus } from '@/shared/ui/loading-status'

import { SecureQueryForm } from './secure-query-form'
import { SecureQueryResult } from './secure-query-result'
import { useSecureQuery } from './use-secure-query'

export function SecureQueryPage() {
  const repository = useMemo(() => new HttpSecureQueryRepository(), [])
  const { state, setPrompt, setDocument, submit, reset } = useSecureQuery(repository)
  const isBusy = state.phase === 'analyzing' || state.phase === 'generating'

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-8">
      <header>
        <h1 className="page-heading">Consultar</h1>
        <p className="page-description">
          Sentinel revisa la consulta y el archivo antes de permitir que el modelo local genere una
          respuesta.
        </p>
      </header>

      <SecureQueryForm
        draft={state.draft}
        isBusy={isBusy}
        onPromptChange={setPrompt}
        onDocumentChange={setDocument}
        onSubmit={submit}
      />

      {state.phase === 'analyzing' && <LoadingStatus message="Analizando el contenido con IA local…" />}
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
          originalPrompt={state.draft.prompt}
          onNewQuery={reset}
        />
      )}
    </div>
  )
}
