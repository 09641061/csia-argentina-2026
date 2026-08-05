import { Clock3, FileCheck2, FlaskConical, LayoutDashboard, LogOut, Menu, MessageSquareText, Settings2, ShieldCheck, UserRound } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { cn } from '@/lib/utils'
import { useAuth } from '@/modules/auth/presentation/auth-provider'

const NAVIGATION = [
  { to: '/', label: 'Consultar', end: true, icon: MessageSquareText },
  { to: '/historial', label: 'Historial', end: false, icon: Clock3 },
  { to: '/seguridad', label: 'Seguridad', end: false, icon: LayoutDashboard },
  { to: '/aprobaciones', label: 'Aprobaciones', end: false, icon: FileCheck2 },
  { to: '/politicas', label: 'Políticas', end: false, icon: Settings2 },
  { to: '/laboratorio', label: 'Laboratorio', end: false, icon: FlaskConical },
]

export function AppLayout() {
  const { session, logout } = useAuth()

  return (
    <div className="flex min-h-svh bg-background">
      <aside className="sticky top-0 hidden h-svh w-64 shrink-0 flex-col border-r bg-card/40 md:flex">
        <NavLink className="flex h-20 items-center gap-3 border-b px-5 text-foreground no-underline" to="/">
          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary text-primary-foreground [&_svg]:size-5">
            <ShieldCheck aria-hidden="true" />
          </span>
          <span className="min-w-0"><strong className="block truncate text-sm">Sentinel AI Guard</strong><small className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">SOC workspace</small></span>
        </NavLink>

        <div className="flex-1 overflow-y-auto px-3 py-5">
          <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">Operaciones</p>
          <nav className="grid gap-1" aria-label="Navegación principal">
            <NavigationLinks />
          </nav>
          <div className="mt-6 rounded-xl border bg-background/30 p-4">
            <div className="flex items-center gap-2 text-xs font-medium"><span className="size-2 rounded-full bg-emerald-400 shadow-[0_0_10px_currentColor]" /> Sistema operativo</div>
            <p className="mt-2 text-[11px] leading-4 text-muted-foreground">Correlación, modelos locales y perímetro conectados.</p>
          </div>
        </div>

        <div className="border-t p-3">
          <div className="flex items-center gap-3 rounded-xl p-2">
            <Avatar size="sm"><AvatarFallback className="text-xs font-semibold">{session?.username.slice(0, 2).toUpperCase()}</AvatarFallback></Avatar>
            <span className="min-w-0 flex-1"><small className="block text-[10px] text-muted-foreground">Sesión activa</small><strong className="block truncate text-xs">{session?.username}</strong></span>
            <Button type="button" variant="ghost" size="icon" onClick={logout} aria-label="Cerrar sesión"><LogOut aria-hidden="true" /></Button>
          </div>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur md:hidden">
          <div className="flex h-16 items-center gap-3 px-4">
            <NavLink className="flex min-w-0 flex-1 items-center gap-2.5 text-foreground no-underline" to="/">
              <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-primary text-primary-foreground [&_svg]:size-5"><ShieldCheck aria-hidden="true" /></span>
              <span className="truncate text-sm font-semibold">Sentinel AI Guard</span>
            </NavLink>
            <Sheet>
              <SheetTrigger asChild><Button variant="outline" size="icon" aria-label="Abrir menú"><Menu aria-hidden="true" /></Button></SheetTrigger>
              <SheetContent side="left" className="w-72">
                <SheetHeader><SheetTitle className="flex items-center gap-2"><ShieldCheck /> Sentinel</SheetTitle></SheetHeader>
                <nav className="grid gap-1 px-4" aria-label="Navegación móvil"><NavigationLinks mobile /></nav>
                <div className="mt-auto"><Separator /><div className="flex items-center gap-3 p-4 text-sm text-muted-foreground"><UserRound className="size-4" aria-hidden="true" /><span className="min-w-0 flex-1 truncate">{session?.username}</span><Button variant="ghost" size="icon" onClick={logout} aria-label="Cerrar sesión"><LogOut /></Button></div></div>
              </SheetContent>
            </Sheet>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[96rem] px-4 py-7 sm:px-6 lg:px-8 lg:py-9">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function NavigationLinks({ mobile = false }: { readonly mobile?: boolean }) {
  return NAVIGATION.map((item) => {
    const Icon = item.icon
    return (
      <NavLink
        key={item.to}
        to={item.to}
        end={item.end}
        className={({ isActive }) => cn(
          'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground no-underline transition-colors hover:bg-muted hover:text-foreground [&_svg]:size-4',
          isActive && 'bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground',
          mobile && 'w-full',
        )}
      >
        <Icon aria-hidden="true" />
        <span className="flex-1">{item.label}</span>
        {!mobile && <span className="size-1.5 rounded-full bg-current opacity-0 group-[.active]:opacity-100" />}
      </NavLink>
    )
  })
}
