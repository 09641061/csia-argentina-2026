import type { AssistantReply, Conversation, ConversationSummary } from './conversation'

export interface ChatRepository {
  list(signal?: AbortSignal): Promise<readonly ConversationSummary[]>
  findById(conversationId: number, signal?: AbortSignal): Promise<Conversation>
  create(prompt: string, signal?: AbortSignal): Promise<AssistantReply>
  send(conversationId: number, prompt: string, signal?: AbortSignal): Promise<AssistantReply>
}

