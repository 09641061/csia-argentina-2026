import { createContext, useContext } from 'react'

import type { ConversationSummary } from '@/contexts/chat/domain/conversation'

export interface ChatContextValue {
  readonly conversations: readonly ConversationSummary[]
  readonly isLoading: boolean
  readonly errorMessage: string | null
  readonly refresh: () => Promise<void>
}

export const ChatContext = createContext<ChatContextValue | null>(null)

export function useChats(): ChatContextValue {
  const value = useContext(ChatContext)
  if (!value) throw new Error('useChats debe utilizarse dentro de ChatProvider')
  return value
}

