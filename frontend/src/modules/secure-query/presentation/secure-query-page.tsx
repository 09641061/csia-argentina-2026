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
    <>
      <h1 className="page-title">Consultar</h1>
      <p className="page-lead">
        Sentinel revisa tu consulta y el documento adjunto antes de que la IA local pueda leerlos.
      </p>

      <SecureQueryForm
        draft={state.draft}
        isBusy={isBusy}
        onPromptChange={setPrompt}
        onDocumentChange={setDocument}
        onSubmit={submit}
      />

      {state.phase === 'analyzing' && <LoadingStatus message="Analizando el contenido…" />}
      {state.phase === 'generating' && (
        <LoadingStatus message="Contenido revisado. Generando la respuesta…" />
      )}

      {state.phase === 'error' && state.errorMessage && (
        <div className="section">
          <ErrorNotice message={state.errorMessage} onRetry={submit} />
        </div>
      )}

      {state.phase === 'done' && state.interaction && (
        <div className="section">
          <SecureQueryResult
            interaction={state.interaction}
            answer={state.answer}
            onNewQuery={reset}
          />
        </div>
      )}
    </>
  )
}
