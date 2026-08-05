import { useCallback, useEffect, useRef, useState } from 'react'

import {
  GetInteraction,
  type InteractionDetail,
} from '@/modules/history/application/get-interaction'
import type { InteractionRepository } from '@/modules/history/domain/interaction-repository'
import { apiErrorMessage } from '@/shared/api/api-error'

export interface InteractionDetailState {
  readonly detail: InteractionDetail | null
  readonly isLoading: boolean
  readonly errorMessage: string | null
}

export function useInteractionDetail(repository: InteractionRepository, interactionId: number) {
  const useCase = useRef(new GetInteraction(repository))
  const [state, setState] = useState<InteractionDetailState>({
    detail: null,
    isLoading: true,
    errorMessage: null,
  })
  const [reloadToken, setReloadToken] = useState(0)

  useEffect(() => {
    if (!Number.isFinite(interactionId) || interactionId < 1) {
      setState({ detail: null, isLoading: false, errorMessage: 'No encontramos esa consulta.' })
      return
    }

    const controller = new AbortController()
    setState((current) => ({ ...current, isLoading: true, errorMessage: null }))

    useCase.current
      .execute(interactionId, controller.signal)
      .then((detail) => {
        if (controller.signal.aborted) return
        setState({ detail, isLoading: false, errorMessage: null })
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        setState({ detail: null, isLoading: false, errorMessage: apiErrorMessage(error) })
      })

    return () => controller.abort()
  }, [interactionId, reloadToken])

  const retry = useCallback(() => setReloadToken((token) => token + 1), [])

  return { ...state, retry }
}
