import type { AssistantReply, Conversation, ConversationSummary } from './conversation'

export interface ChatRepository {
  list(signal?: AbortSignal): Promise<readonly ConversationSummary[]>
  findById(conversationId: number, signal?: AbortSignal): Promise<Conversation>
  create(prompt: string, attachment?: File | null, signal?: AbortSignal): Promise<AssistantReply>
  send(conversationId: number, prompt: string, attachment?: File | null, signal?: AbortSignal): Promise<AssistantReply>
}
