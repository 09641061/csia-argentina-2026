export type MessageRole = 'user' | 'assistant'

export interface ChatMessage {
  readonly id: number
  readonly role: MessageRole
  readonly content: string
  readonly attachmentUrl?: string | null
  readonly attachmentName?: string | null
  readonly attachmentMimeType?: string | null
  readonly createdAt: string
}

export interface ConversationSummary {
  readonly id: number
  readonly title: string
  readonly createdAt: string
  readonly updatedAt: string
}

export interface Conversation extends ConversationSummary {
  readonly messages: readonly ChatMessage[]
}

export interface AssistantReply {
  readonly conversationId: number
  readonly answer: string
  readonly modelName: string
  readonly generatedAt: string
}
