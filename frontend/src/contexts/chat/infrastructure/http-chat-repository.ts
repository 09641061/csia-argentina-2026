import type { ChatRepository } from '@/contexts/chat/domain/chat-repository'
import type {
  AssistantReply,
  ChatMessage,
  Conversation,
  ConversationSummary,
} from '@/contexts/chat/domain/conversation'
import { request } from '@/shared/infrastructure/api/http-client'
import type {
  ChatMessageResource,
  ChatMessageResponseResource,
  ConversationResource,
  ConversationSummaryResource,
} from '@/shared/infrastructure/api/resources'

export class HttpChatRepository implements ChatRepository {
  async list(signal?: AbortSignal): Promise<readonly ConversationSummary[]> {
    const resources = await request<ConversationSummaryResource[]>('/api/v1/chat/conversations', {
      signal,
      timeoutMs: 20_000,
    })
    return resources.map(toConversationSummary)
  }

  async findById(conversationId: number, signal?: AbortSignal): Promise<Conversation> {
    const resource = await request<ConversationResource>(
      `/api/v1/chat/conversations/${conversationId}`,
      { signal, timeoutMs: 20_000 },
    )
    return {
      ...toConversationSummary(resource),
      messages: resource.messages.map(toMessage),
    }
  }

  create(prompt: string, signal?: AbortSignal): Promise<AssistantReply> {
    return this.post('/api/v1/chat/conversations', prompt, signal)
  }

  send(conversationId: number, prompt: string, signal?: AbortSignal): Promise<AssistantReply> {
    return this.post(`/api/v1/chat/conversations/${conversationId}/messages`, prompt, signal)
  }

  private async post(path: string, prompt: string, signal?: AbortSignal): Promise<AssistantReply> {
    const body = new FormData()
    body.append('prompt', prompt)
    const resource = await request<ChatMessageResponseResource>(path, {
      method: 'POST',
      body,
      signal,
    })
    return {
      conversationId: resource.conversation_id,
      answer: resource.answer,
      modelName: resource.model_name,
      generatedAt: resource.generated_at,
    }
  }
}

function toConversationSummary(resource: ConversationSummaryResource): ConversationSummary {
  return {
    id: resource.id,
    title: resource.title || 'Nueva conversación',
    createdAt: resource.created_at,
    updatedAt: resource.updated_at,
  }
}

function toMessage(resource: ChatMessageResource): ChatMessage {
  return {
    id: resource.id,
    role: resource.role === 'assistant' ? 'assistant' : 'user',
    content: resource.content,
    createdAt: resource.created_at,
  }
}

