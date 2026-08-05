import { useCallback, useEffect, useRef, useState } from 'react'

import { GetInteractionHistory } from '@/modules/history/application/get-interaction-history'
import type {
  InteractionPage,
  InteractionRepository,
} from '@/modules/history/domain/interaction-repository'
import { apiErrorMessage } from '@/shared/api/api-error'

export interface HistoryState {
  readonly page: InteractionPage | null
  readonly isLoading: boolean
  readonly errorMessage: string | null
}

export function useInteractionHistory(repository: InteractionRepository, page: number) {
  const useCase = useRef(new GetInteractionHistory(repository))
  const [state, setState] = useState<HistoryState>({
    page: null,
    isLoading: true,
    errorMessage: null,
  })
  const [reloadToken, setReloadToken] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setState((current) => ({ ...current, isLoading: true, errorMessage: null }))

    useCase.current
      .execute(page, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return
        setState({ page: result, isLoading: false, errorMessage: null })
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        setState({ page: null, isLoading: false, errorMessage: apiErrorMessage(error) })
      })

    return () => controller.abort()
  }, [page, reloadToken])

  const retry = useCallback(() => setReloadToken((token) => token + 1), [])

  return { ...state, retry }
}
