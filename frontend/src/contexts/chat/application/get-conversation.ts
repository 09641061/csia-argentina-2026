import type { ChatRepository } from '@/contexts/chat/domain/chat-repository'

export class GetConversation {
  private readonly repository: ChatRepository
  constructor(repository: ChatRepository) { this.repository = repository }

  execute(conversationId: number, signal?: AbortSignal) {
    if (!Number.isInteger(conversationId) || conversationId < 1) {
      throw new Error('La conversación solicitada no es válida.')
    }
    return this.repository.findById(conversationId, signal)
  }
}
