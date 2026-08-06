import type { ChatRepository } from '@/contexts/chat/domain/chat-repository'

export class SendMessage {
  private readonly repository: ChatRepository
  constructor(repository: ChatRepository) { this.repository = repository }

  execute(conversationId: number | null, prompt: string, signal?: AbortSignal) {
    const cleanPrompt = prompt.trim()
    if (!cleanPrompt) throw new Error('Escribe un mensaje para continuar.')
    if (cleanPrompt.length > 8_000) throw new Error('El mensaje no puede superar 8.000 caracteres.')
    return conversationId === null
      ? this.repository.create(cleanPrompt, signal)
      : this.repository.send(conversationId, cleanPrompt, signal)
  }
}
