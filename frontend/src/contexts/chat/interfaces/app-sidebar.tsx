import { ChevronDown, FileSearch, Menu, MessageCircle, PanelLeftClose, Plus, Search, ShieldCheck } from 'lucide-react'
import { Link, NavLink, useLocation } from 'react-router-dom'

import { UserProfileMenu } from '@/contexts/iam/interfaces/user-profile-menu'
import { ClaudeWordmark } from '@/shared/interfaces/components/claude-brand'
import { SystemHealthStatus } from '@/shared/interfaces/components/system-health-status'
import { Button } from '@/shared/interfaces/ui/button'
import { Sheet, SheetClose, SheetContent, SheetTitle, SheetTrigger } from '@/shared/interfaces/ui/sheet'
import { cn } from '@/shared/interfaces/utils'

import { useChats } from './chat-context'

const NAVIGATION = [
  { to: '/chats', label: 'Chats', icon: MessageCircle, match: ['/chats', '/chat/'] },
  { to: '/consulta-segura', label: 'Consulta segura', icon: ShieldCheck, match: ['/consulta-segura'] },
  { to: '/analisis', label: 'Análisis', icon: FileSearch, match: ['/analisis'] },
] as const

export function AppSidebar() {
  return <aside className="hidden h-svh w-[280px] shrink-0 border-r border-white/[0.08] bg-[#151514] md:flex md:flex-col"><SidebarContent /></aside>
}

export function MobileSidebar() {
  return <Sheet><SheetTrigger asChild><Button variant="ghost" size="icon" className="text-[#c8c6bd] hover:bg-white/[0.06] md:hidden" aria-label="Abrir menú"><Menu /></Button></SheetTrigger><SheetContent side="left" className="w-[280px] gap-0 border-r border-white/[0.08] bg-[#151514] p-0" showCloseButton={false}><SheetTitle className="sr-only">Navegación principal</SheetTitle><SidebarContent mobile /></SheetContent></Sheet>
}

function SidebarContent({ mobile = false }: { readonly mobile?: boolean }) {
  const { conversations, isLoading } = useChats()
  const location = useLocation()
  const recent = conversations.slice(0, 5)
  const wrap = (child: React.ReactElement, key: string) => mobile ? <SheetClose key={key} asChild>{child}</SheetClose> : child

  return <div className="flex min-h-0 flex-1 flex-col text-[#e8e6de]">
    <div className="flex h-[68px] items-center justify-between px-5">
      <ClaudeWordmark className="w-[96px]" />
      <div className="flex items-center gap-1"><Button type="button" variant="ghost" size="icon-sm" className="text-[#b0aea5] hover:bg-white/[0.06]" aria-label="Buscar chats" asChild><Link to="/chats"><Search /></Link></Button><span className="hidden md:grid"><PanelLeftClose className="size-[17px] text-[#8e8c84]" aria-hidden="true" /></span><SystemHealthStatus /></div>
    </div>

    <nav className="px-3 pt-2" aria-label="Navegación principal">
      {wrap(<NavLink to="/" end className={({ isActive }) => navClass(isActive)}><span className="grid size-7 place-items-center rounded-full bg-white/[0.07]"><Plus className="size-[18px]" /></span><span>Nuevo chat</span></NavLink>, 'new')}
      <div className="mt-1 space-y-0.5">
        {NAVIGATION.map((item) => {
          const active = item.match.some((path) => path.endsWith('/') ? location.pathname.startsWith(path) : location.pathname === path || location.pathname.startsWith(`${path}/`))
          const link = <Link key={item.to} to={item.to} className={navClass(active)}><item.icon className="size-[19px]" /><span>{item.label}</span></Link>
          return wrap(link, item.to)
        })}
        {wrap(<Link to="/auditoria" className={navClass(location.pathname.startsWith('/auditoria'))}><ShieldCheck className="size-[19px]" /><span>Auditoría</span></Link>, 'audit')}
      </div>
    </nav>

    <section className="mt-8 min-h-0 px-3" aria-labelledby="recents-title">
      <div className="mb-2 flex items-center justify-between px-2"><h2 id="recents-title" className="text-xs font-normal text-[#8e8c84]">Recientes</h2><span className="text-[#77766f]" title="Ordenados por actividad"><ChevronDown className="size-4" /></span></div>
      <div className="space-y-0.5">
        {isLoading && <p className="px-2 py-2 text-xs text-[#77766f]">Cargando chats…</p>}
        {!isLoading && recent.length === 0 && <p className="px-2 py-2 text-xs leading-5 text-[#77766f]">Tus conversaciones aparecerán aquí.</p>}
        {recent.map((conversation) => wrap(<Link to={`/chat/${conversation.id}`} className={cn('block truncate rounded-lg px-2.5 py-2 text-[13px] text-[#c8c6bd] no-underline transition hover:bg-white/[0.05] hover:text-white', location.pathname === `/chat/${conversation.id}` && 'bg-black/30 text-white')} title={conversation.title}>{conversation.title}</Link>, `recent-${conversation.id}`))}
      </div>
      {conversations.length > 0 && wrap(<Link to="/chats" className="mt-1 flex items-center gap-2 rounded-lg px-2.5 py-2 text-xs text-[#8e8c84] no-underline transition hover:bg-white/[0.05] hover:text-white"><ChevronDown className="size-4" /> Ver todos los chats</Link>, 'all-chats')}
    </section>

    <div className="mt-auto border-t border-white/[0.08] p-3"><UserProfileMenu /></div>
  </div>
}

function navClass(active: boolean): string {
  return cn('flex min-h-10 items-center gap-3 rounded-xl px-2.5 text-[14px] text-[#d6d4cc] no-underline transition hover:bg-white/[0.055] hover:text-white', active && 'bg-black/30 text-white')
}

