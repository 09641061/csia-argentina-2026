import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'

import { ListConversations } from '@/contexts/chat/application/list-conversations'
import type { ConversationSummary } from '@/contexts/chat/domain/conversation'
import { HttpChatRepository } from '@/contexts/chat/infrastructure/http-chat-repository'
import { apiErrorMessage } from '@/shared/infrastructure/api/api-error'

import { ChatContext } from './chat-context'

export function ChatProvider({ children }: { readonly children: ReactNode }) {
  const repository = useMemo(() => new HttpChatRepository(), [])
  const useCase = useRef(new ListConversations(repository))
  const [conversations, setConversations] = useState<readonly ConversationSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      setConversations(await useCase.current.execute())
    } catch (error) {
      setErrorMessage(apiErrorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return (
    <ChatContext.Provider value={{ conversations, isLoading, errorMessage, refresh }}>
      {children}
    </ChatContext.Provider>
  )
}

