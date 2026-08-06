import { ArrowUp, FileJson2, Paperclip, X } from 'lucide-react'
import { useEffect, useId, useRef, useState, type ChangeEvent, type FormEvent, type KeyboardEvent } from 'react'

import { Button } from '@/shared/interfaces/ui/button'
import { Spinner } from '@/shared/interfaces/ui/spinner'
import { Textarea } from '@/shared/interfaces/ui/textarea'

interface ChatComposerProps {
  readonly value: string
  readonly attachment: File | null
  readonly isSending: boolean
  readonly onChange: (value: string) => void
  readonly onAttachmentChange: (file: File | null) => void
  readonly onSubmit: () => void
}

export function ChatComposer({ value, attachment, isSending, onChange, onAttachmentChange, onSubmit }: ChatComposerProps) {
  const id = useId()
  const fileId = `${id}-attachment`
  const inputRef = useRef<HTMLInputElement>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  useEffect(() => {
    if (!attachment || !attachment.type.startsWith('image/')) {
      setPreviewUrl(null)
      return
    }
    const url = URL.createObjectURL(attachment)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [attachment])

  const canSubmit = Boolean(value.trim() || attachment)
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!isSending && canSubmit) onSubmit()
  }
  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      if (!isSending && canSubmit) onSubmit()
    }
  }
  const chooseFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null
    if (file) onAttachmentChange(file)
    event.target.value = ''
  }

  return (
    <form onSubmit={submit} className="overflow-hidden rounded-[24px] border border-white/[0.055] bg-[#363633] shadow-[0_18px_55px_rgba(0,0,0,0.24)] transition focus-within:border-white/[0.10]">
      {attachment && (
        <div className="flex gap-3 px-4 pt-4">
          <div className="group relative overflow-hidden rounded-xl border border-white/15 bg-[#20201f]">
            {previewUrl ? <img src={previewUrl} alt={attachment.name} className="h-24 w-32 object-cover" /> : <div className="flex h-24 w-32 flex-col items-center justify-center gap-2 px-2 text-center text-xs text-[#c9c7bf]"><FileJson2 className="size-7" /><span className="line-clamp-2">{attachment.name}</span></div>}
            <button type="button" onClick={() => onAttachmentChange(null)} className="absolute right-1.5 top-1.5 grid size-6 place-items-center rounded-full bg-black/70 text-white" aria-label="Quitar archivo"><X className="size-4" /></button>
          </div>
        </div>
      )}
      <label className="sr-only" htmlFor={id}>Mensaje</label>
      <Textarea id={id} value={value} onChange={(event) => onChange(event.target.value)} onKeyDown={handleKeyDown} placeholder="¿Cómo puedo ayudarte hoy?" rows={2} maxLength={8_000} disabled={isSending} className="min-h-[76px] resize-none border-0 bg-transparent px-5 pb-2 pt-4 text-[16px] leading-6 text-[#f1efe8] shadow-none placeholder:text-[#aaa89f] focus-visible:ring-0" />
      <div className="flex items-center gap-2 px-3 pb-3">
        <input ref={inputRef} id={fileId} type="file" accept="application/json,image/png,image/jpeg,image/webp" className="sr-only" onChange={chooseFile} disabled={isSending} />
        <Button type="button" variant="ghost" size="icon" className="size-9 rounded-full border border-white/15 text-[#d6d4cc] hover:bg-white/[0.07]" onClick={() => inputRef.current?.click()} disabled={isSending} aria-label="Adjuntar JSON, PNG, JPEG o WebP" title="Adjuntar JSON, PNG, JPEG o WebP"><Paperclip className="size-[18px]" /></Button>
        <span className="ml-1 text-xs text-[#aaa89f]">Gemma local</span>
        <Button type="submit" size="icon" className="ml-auto size-9 rounded-full bg-[#eceae3] text-[#222220] hover:bg-white disabled:bg-[#65645f] disabled:text-[#97968f]" disabled={isSending || !canSubmit} aria-label="Enviar mensaje">{isSending ? <Spinner className="size-4" /> : <ArrowUp className="size-[18px]" />}</Button>
      </div>
    </form>
  )
}
