import { ArrowUp, Paperclip } from 'lucide-react'
import { useId, type FormEvent, type KeyboardEvent } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/shared/interfaces/ui/button'
import { Spinner } from '@/shared/interfaces/ui/spinner'
import { Textarea } from '@/shared/interfaces/ui/textarea'

interface ChatComposerProps {
  readonly value: string
  readonly isSending: boolean
  readonly onChange: (value: string) => void
  readonly onSubmit: () => void
}

export function ChatComposer({ value, isSending, onChange, onSubmit }: ChatComposerProps) {
  const id = useId()

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!isSending && value.trim()) onSubmit()
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      if (!isSending && value.trim()) onSubmit()
    }
  }

  return (
    <form
      onSubmit={submit}
      className="overflow-hidden rounded-[24px] border border-white/[0.055] bg-[#363633] shadow-[0_18px_55px_rgba(0,0,0,0.24)] transition focus-within:border-white/[0.10] focus-within:shadow-[0_20px_65px_rgba(0,0,0,0.3)]"
    >
      <label className="sr-only" htmlFor={id}>Mensaje</label>
      <Textarea
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="¿Cómo puedo ayudarte hoy?"
        rows={2}
        maxLength={8_000}
        disabled={isSending}
        className="min-h-[76px] resize-none border-0 bg-transparent px-5 pb-2 pt-4 text-[16px] leading-6 text-[#f1efe8] shadow-none placeholder:text-[#aaa89f] focus-visible:ring-0"
      />
      <div className="flex items-center gap-2 px-3 pb-3">
        <Button
          asChild
          variant="ghost"
          size="icon"
          className="size-9 rounded-full border border-white/15 text-[#d6d4cc] hover:bg-white/[0.07]"
        >
          <Link to="/consulta-segura" title="Adjuntar archivo en Consulta segura" aria-label="Abrir Consulta segura para adjuntar un archivo">
            <Paperclip className="size-[18px]" aria-hidden="true" />
          </Link>
        </Button>
        <span className="ml-1 text-xs text-[#aaa89f]">Sentinel local</span>
        <Button
          type="submit"
          size="icon"
          className="ml-auto size-9 rounded-full bg-[#eceae3] text-[#222220] hover:bg-white disabled:bg-[#65645f] disabled:text-[#97968f]"
          disabled={isSending || !value.trim()}
          aria-label="Enviar mensaje"
        >
          {isSending ? <Spinner className="size-4" /> : <ArrowUp className="size-[18px]" />}
        </Button>
      </div>
    </form>
  )
}
