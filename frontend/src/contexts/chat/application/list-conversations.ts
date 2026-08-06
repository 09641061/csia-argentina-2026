import type { ChatRepository } from '@/contexts/chat/domain/chat-repository'

export class ListConversations {
  private readonly repository: ChatRepository
  constructor(repository: ChatRepository) { this.repository = repository }

  execute(signal?: AbortSignal) {
    return this.repository.list(signal)
  }
}
