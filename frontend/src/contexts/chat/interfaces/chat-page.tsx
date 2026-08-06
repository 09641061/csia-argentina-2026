import { Copy, RotateCcw } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { GetConversation } from '@/contexts/chat/application/get-conversation'
import { SendMessage } from '@/contexts/chat/application/send-message'
import type { ChatMessage, Conversation } from '@/contexts/chat/domain/conversation'
import { HttpChatRepository } from '@/contexts/chat/infrastructure/http-chat-repository'
import { useOptionalAuth } from '@/contexts/iam/interfaces/auth-context'
import { apiErrorMessage } from '@/shared/infrastructure/api/api-error'
import { ClaudeSpark } from '@/shared/interfaces/components/claude-brand'
import { ErrorNotice } from '@/shared/interfaces/components/error-notice'
import { LoadingStatus } from '@/shared/interfaces/components/loading-status'
import { Button } from '@/shared/interfaces/ui/button'

import { ChatComposer } from './chat-composer'
import { useChats } from './chat-context'

export function ChatPage() {
  const repository = useMemo(() => new HttpChatRepository(), [])
  const getConversation = useRef(new GetConversation(repository))
  const sendMessage = useRef(new SendMessage(repository))
  const { conversationId } = useParams()
  const parsedId = conversationId ? Number.parseInt(conversationId, 10) : null
  const navigate = useNavigate()
  const auth = useOptionalAuth()
  const { refresh } = useChats()
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [prompt, setPrompt] = useState('')
  const [attachment, setAttachment] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(parsedId !== null)
  const [isSending, setIsSending] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const load = useCallback(async (id: number, signal?: AbortSignal) => {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      setConversation(await getConversation.current.execute(id, signal))
    } catch (error) {
      if (!signal?.aborted) setErrorMessage(apiErrorMessage(error))
    } finally {
      if (!signal?.aborted) setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (parsedId === null) {
      setConversation(null)
      setIsLoading(false)
      setErrorMessage(null)
      return
    }
    const controller = new AbortController()
    void load(parsedId, controller.signal)
    return () => controller.abort()
  }, [parsedId, load])

  const submit = async () => {
    const submitted = prompt.trim()
    if ((!submitted && !attachment) || isSending) return
    const submittedAttachment = attachment
    setPrompt('')
    setAttachment(null)
    setErrorMessage(null)
    setIsSending(true)
    if (conversation) {
      const optimistic: ChatMessage = {
        id: -Date.now(),
        role: 'user',
        content: submitted,
        createdAt: new Date().toISOString(),
      }
      setConversation({ ...conversation, messages: [...conversation.messages, optimistic] })
    }
    try {
      const reply = await sendMessage.current.execute(parsedId, submitted, submittedAttachment)
      await refresh()
      if (parsedId === null) {
        navigate(`/chat/${reply.conversationId}`, { replace: true })
      } else {
        await load(reply.conversationId)
      }
    } catch (error) {
      const message = apiErrorMessage(error)
      setPrompt(submitted)
      setAttachment(submittedAttachment)
      if (parsedId !== null) await load(parsedId)
      setErrorMessage(message)
    } finally {
      setIsSending(false)
    }
  }

  if (parsedId === null) {
    const username = auth?.session?.username?.split(/[._-]/)[0]
    return (
      <div className="flex min-h-full items-center justify-center bg-[#1b1b1a] px-4 pb-10 pt-20 text-[#f3f1ea] sm:px-8">
        <section className="w-full max-w-[820px] -translate-y-6">
          <header className="mb-10 flex items-center justify-center gap-4 text-center">
            <ClaudeSpark className="size-10 sm:size-12" />
            <h1 className="font-serif text-[34px] font-normal tracking-[-0.035em] text-[#c9c7bf] sm:text-[44px]">
              {username ? `¿En qué puedo ayudarte, ${username}?` : '¿En qué puedo ayudarte?'}
            </h1>
          </header>
          <ChatComposer value={prompt} attachment={attachment} isSending={isSending} onChange={setPrompt} onAttachmentChange={setAttachment} onSubmit={submit} />
          {errorMessage && <div className="mt-4"><ErrorNotice message={errorMessage} onRetry={submit} /></div>}
          <p className="mt-3 text-center text-[11px] text-[#8b8983]">
            Claude revisa cada mensaje antes de enviarlo al modelo local.
          </p>
        </section>
      </div>
    )
  }

  return (
    <div className="relative flex min-h-full flex-col bg-[#1b1b1a] text-[#f3f1ea]">
      <div className="mx-auto w-full max-w-[800px] flex-1 px-5 pb-48 pt-24 sm:px-8">
        {isLoading && !conversation && <LoadingStatus message="Cargando la conversación…" />}
        {errorMessage && !conversation && <ErrorNotice message={errorMessage} onRetry={() => parsedId && load(parsedId)} />}
        {conversation && (
          <>
            <h1 className="sr-only">{conversation.title}</h1>
            <div className="space-y-9" aria-live="polite">
              {conversation.messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {isSending && (
                  <div className="flex items-center gap-3 text-sm text-[#85847d]">
                  <ClaudeSpark className="size-6 animate-pulse" /> Pensando…
                </div>
              )}
            </div>
          </>
        )}
      </div>
      <div className="pointer-events-none fixed bottom-0 right-0 z-20 w-full bg-gradient-to-t from-[#1b1b1a] via-[#1b1b1a] to-transparent px-4 pb-5 pt-12 md:left-[280px] md:w-[calc(100%-280px)]">
        <div className="pointer-events-auto mx-auto max-w-[800px]">
          {errorMessage && conversation && <div className="mb-3"><ErrorNotice message={errorMessage} onRetry={submit} /></div>}
          <ChatComposer value={prompt} attachment={attachment} isSending={isSending} onChange={setPrompt} onAttachmentChange={setAttachment} onSubmit={submit} />
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ message }: { readonly message: ChatMessage }) {
  const copy = () => void navigator.clipboard?.writeText(message.content)
  if (message.role === 'user') {
    return (
      <article className="ml-auto w-fit max-w-[82%] rounded-[20px] bg-[#30302e] px-4 py-3 text-[15px] leading-7 text-[#f1efe8]">
        {message.attachmentUrl && message.attachmentMimeType?.startsWith('image/') && <img src={message.attachmentUrl} alt={message.attachmentName ?? 'Imagen adjunta'} className="mb-3 max-h-72 rounded-xl object-contain" />}
        {message.attachmentUrl && !message.attachmentMimeType?.startsWith('image/') && <a href={message.attachmentUrl} target="_blank" rel="noreferrer" className="mb-2 block text-sm underline">{message.attachmentName ?? 'Archivo adjunto'}</a>}
        <p className="whitespace-pre-wrap">{message.content}</p>
      </article>
    )
  }
  return (
    <article className="group flex gap-3">
      <ClaudeSpark className="mt-1 size-7 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="whitespace-pre-wrap text-[15px] leading-7 text-[#efede6]">{message.content}</p>
        <div className="mt-3 flex gap-1 opacity-0 transition group-hover:opacity-100 group-focus-within:opacity-100">
          <Button type="button" variant="ghost" size="icon-sm" onClick={copy} aria-label="Copiar respuesta" className="text-[#77756f]">
            <Copy aria-hidden="true" />
          </Button>
          <Button type="button" variant="ghost" size="icon-sm" disabled aria-label="Volver a generar" className="text-[#77756f]">
            <RotateCcw aria-hidden="true" />
          </Button>
        </div>
      </div>
    </article>
  )
}
