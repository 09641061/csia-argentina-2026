import { Check, ChevronDown, MoreVertical, Search, SquarePen } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { formatDateTime } from '@/shared/lib/format'
import { EmptyState } from '@/shared/interfaces/components/empty-state'
import { ErrorNotice } from '@/shared/interfaces/components/error-notice'
import { LoadingStatus } from '@/shared/interfaces/components/loading-status'
import { Button } from '@/shared/interfaces/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/shared/interfaces/ui/dropdown-menu'
import { Input } from '@/shared/interfaces/ui/input'

import { useChats } from './chat-context'

export function ChatsPage() {
  const { conversations, isLoading, errorMessage, refresh } = useChats()
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<'all' | 'week'>('all')
  const [isSelecting, setIsSelecting] = useState(false)
  const [selected, setSelected] = useState<ReadonlySet<number>>(new Set())
  const filtered = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase('es')
    const oldest = Date.now() - 7 * 24 * 60 * 60 * 1_000
    return conversations.filter((item) => {
      const matchesText = !needle || item.title.toLocaleLowerCase('es').includes(needle)
      const matchesDate = filter === 'all' || new Date(item.updatedAt).getTime() >= oldest
      return matchesText && matchesDate
    })
  }, [conversations, filter, query])

  const toggle = (id: number) => {
    setSelected((current) => {
      const next = new Set(current)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  return (
    <div className="min-h-full bg-[#1b1b1a] px-5 pb-16 pt-24 text-[#f3f1ea] sm:px-8 lg:px-12">
      <section className="mx-auto w-full max-w-[1040px]">
        <header className="mb-10 flex flex-wrap items-center justify-between gap-4">
          <h1 className="font-serif text-[34px] tracking-[-0.03em] sm:text-[38px]">Chats</h1>
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[#77756f]" />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Buscar chats"
                aria-label="Buscar chats"
                className="h-10 w-11 rounded-xl border-0 bg-[#30302e] pl-9 text-[#f3f1ea] transition-all placeholder:text-transparent focus:w-56 focus:placeholder:text-[#8e8c84] sm:w-56 sm:placeholder:text-[#8e8c84]"
              />
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild><Button variant="secondary" className="rounded-xl bg-[#30302e] text-[#f3f1ea] hover:bg-[#393936]">Filtrar por <strong>{filter === 'all' ? 'Todo' : '7 días'}</strong> <ChevronDown aria-hidden="true" /></Button></DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="border-white/10 bg-[#292927] text-[#f3f1ea]"><DropdownMenuItem onSelect={() => setFilter('all')} className="focus:bg-white/[0.07] focus:text-white">Todo</DropdownMenuItem><DropdownMenuItem onSelect={() => setFilter('week')} className="focus:bg-white/[0.07] focus:text-white">Últimos 7 días</DropdownMenuItem></DropdownMenuContent>
            </DropdownMenu>
            <Button
              variant="secondary"
              className="rounded-xl bg-[#30302e] text-[#f3f1ea] hover:bg-[#393936]"
              onClick={() => { setIsSelecting((value) => !value); setSelected(new Set()) }}
            >
              {isSelecting ? 'Listo' : 'Seleccionar chats'}
            </Button>
            <Button asChild className="rounded-xl bg-[#eceae3] text-[#222220] hover:bg-white">
              <Link to="/"><SquarePen aria-hidden="true" /> Nuevo chat</Link>
            </Button>
          </div>
        </header>

        {isSelecting && selected.size > 0 && (
          <p className="mb-3 text-sm text-[#85847d]">{selected.size} {selected.size === 1 ? 'chat seleccionado' : 'chats seleccionados'}</p>
        )}
        {isLoading && <LoadingStatus message="Cargando tus chats…" />}
        {errorMessage && !isLoading && <ErrorNotice message={errorMessage} onRetry={refresh} />}
        {!isLoading && !errorMessage && filtered.length === 0 && (
          <EmptyState
            title={query ? 'No hay coincidencias' : 'Todavía no hay chats'}
            description={query ? 'Prueba con otro término de búsqueda.' : 'Inicia una conversación y aparecerá aquí.'}
          />
        )}
        {!isLoading && filtered.length > 0 && (
          <div className="divide-y divide-white/[0.07]">
            {filtered.map((conversation, index) => {
              const active = selected.has(conversation.id)
              return (
                <article key={conversation.id} className="group relative">
                  {isSelecting ? (
                    <button
                      type="button"
                      className={`flex min-h-[62px] w-full items-center gap-3 rounded-xl px-4 text-left transition ${active || index === 0 ? 'bg-[#292927]' : 'hover:bg-white/[0.035]'}`}
                      onClick={() => toggle(conversation.id)}
                    >
                      <span className={`grid size-5 place-items-center rounded border ${active ? 'border-[#eceae3] bg-[#eceae3] text-[#222220]' : 'border-white/20'}`}>
                        {active && <Check className="size-3.5" aria-hidden="true" />}
                      </span>
                      <span className="truncate text-[15px] font-medium">{conversation.title}</span>
                      <time className="ml-auto shrink-0 text-sm text-[#85847d]">{formatConversationDate(conversation.updatedAt)}</time>
                    </button>
                  ) : (
                    <Link
                      to={`/chat/${conversation.id}`}
                      className={`flex min-h-[62px] items-center gap-3 rounded-xl px-4 text-[15px] font-medium text-[#efede6] no-underline transition ${index === 0 ? 'bg-[#292927]' : 'hover:bg-white/[0.035]'}`}
                    >
                      <span className="truncate">{conversation.title}</span>
                      <time className="ml-auto shrink-0 text-sm font-normal text-[#85847d]">{formatConversationDate(conversation.updatedAt)}</time>
                      <MoreVertical className="size-5 shrink-0 opacity-0 transition group-hover:opacity-100" aria-hidden="true" />
                    </Link>
                  )}
                </article>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}

function formatConversationDate(value: string): string {
  const date = new Date(value)
  const now = new Date()
  if (date.toDateString() === now.toDateString()) return 'Hoy'
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) return 'Ayer'
  return Number.isNaN(date.getTime()) ? formatDateTime(value) : new Intl.DateTimeFormat('es', { day: 'numeric', month: 'short', year: date.getFullYear() === now.getFullYear() ? undefined : 'numeric' }).format(date)
}
