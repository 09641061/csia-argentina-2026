import { useCallback, useEffect, useRef, useState } from 'react'

import { SubmitSecureQuery } from '@/contexts/analysis-and-decision/application/secure-query/submit-secure-query'
import type { AssistantResponse } from '@/contexts/analysis-and-decision/domain/secure-query/assistant-response'
import type { SecureInteraction } from '@/contexts/analysis-and-decision/domain/secure-query/secure-interaction'
import {
  emptyDraft,
  type SecureQueryDraft,
} from '@/contexts/analysis-and-decision/domain/secure-query/secure-query-draft'
import type { SecureQueryRepository } from '@/contexts/analysis-and-decision/domain/secure-query/secure-query-repository'
import { apiErrorMessage } from '@/shared/infrastructure/api/api-error'

export type SecureQueryPhase = 'idle' | 'analyzing' | 'generating' | 'done' | 'error'

export interface SecureQueryState {
  readonly draft: SecureQueryDraft
  readonly phase: SecureQueryPhase
  readonly interaction: SecureInteraction | null
  readonly answer: AssistantResponse | null
  readonly errorMessage: string | null
}

/**
 * Drives the one interaction the product supports.
 *
 * A submission in flight blocks a second one and is aborted when the screen
 * goes away, so a duplicated request can never produce two audited
 * interactions for one click.
 */
export function useSecureQuery(repository: SecureQueryRepository) {
  const useCase = useRef(new SubmitSecureQuery(repository))
  const inFlight = useRef<AbortController | null>(null)
  const [state, setState] = useState<SecureQueryState>({
    draft: emptyDraft(),
    phase: 'idle',
    interaction: null,
    answer: null,
    errorMessage: null,
  })

  useEffect(() => {
    return () => inFlight.current?.abort()
  }, [])

  const setPrompt = useCallback((prompt: string) => {
    setState((current) => ({ ...current, draft: { ...current.draft, prompt } }))
  }, [])

  const setDocument = useCallback((document: File | null) => {
    setState((current) => ({ ...current, draft: { ...current.draft, document } }))
  }, [])

  const reset = useCallback(() => {
    inFlight.current?.abort()
    inFlight.current = null
    setState({
      draft: emptyDraft(),
      phase: 'idle',
      interaction: null,
      answer: null,
      errorMessage: null,
    })
  }, [])

  const submit = useCallback(async () => {
    if (inFlight.current) return

    const controller = new AbortController()
    inFlight.current = controller
    const hasQuestion = state.draft.prompt.trim().length > 0

    setState((current) => ({
      ...current,
      phase: 'analyzing',
      interaction: null,
      answer: null,
      errorMessage: null,
    }))

    // The backend reviews and then answers in a single call; the intermediate
    // label exists so the person knows a longer wait is expected when a
    // question was asked.
    const generationHint = hasQuestion
      ? window.setTimeout(() => {
          setState((current) => (current.phase === 'analyzing' ? { ...current, phase: 'generating' } : current))
        }, 1200)
      : undefined

    try {
      const outcome = await useCase.current.execute(state.draft, controller.signal)
      setState((current) => ({
        ...current,
        phase: 'done',
        interaction: outcome.interaction,
        answer: outcome.answer,
        errorMessage: null,
      }))
    } catch (error) {
      if (controller.signal.aborted) return
      setState((current) => ({
        ...current,
        phase: 'error',
        interaction: null,
        answer: null,
        errorMessage: apiErrorMessage(error),
      }))
    } finally {
      if (generationHint !== undefined) window.clearTimeout(generationHint)
      inFlight.current = null
    }
  }, [state.draft])

  return { state, setPrompt, setDocument, submit, reset }
}
