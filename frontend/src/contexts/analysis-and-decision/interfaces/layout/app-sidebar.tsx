import { Clock3, Menu, ShieldCheck, SquarePen } from 'lucide-react'
import { NavLink } from 'react-router-dom'

import { UserProfileMenu } from '@/contexts/iam/interfaces/user-profile-menu'
import { ClaudeWordmark } from '@/shared/interfaces/components/claude-brand'
import { cn } from '@/shared/interfaces/utils'
import { Button } from '@/shared/interfaces/ui/button'
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from '@/shared/interfaces/ui/sheet'

const NAVIGATION = [
  { to: '/', label: 'Consultar', end: true, icon: SquarePen },
  { to: '/historial', label: 'Historial', end: false, icon: Clock3 },
] as const

export function AppSidebar() {
  return (
    <aside className="hidden h-svh w-[292px] shrink-0 border-r border-white/[0.08] bg-[#151514] md:flex md:flex-col">
      <SidebarContent />
    </aside>
  )
}

export function MobileSidebar() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="text-[#c8c6bd] hover:bg-white/[0.06] md:hidden"
          aria-label="Abrir menú"
        >
          <Menu aria-hidden="true" />
        </Button>
      </SheetTrigger>
      <SheetContent
        side="left"
        className="w-[292px] gap-0 border-r border-white/[0.08] bg-[#151514] p-0"
        showCloseButton={false}
      >
        <SheetTitle className="sr-only">Navegación principal</SheetTitle>
        <SidebarContent mobile />
      </SheetContent>
    </Sheet>
  )
}

function SidebarContent({ mobile = false }: { readonly mobile?: boolean }) {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex h-[74px] items-center justify-between px-5">
        <div className="min-w-0">
          <ClaudeWordmark className="w-[104px]" />
          <span className="mt-1 block text-[10px] font-medium uppercase tracking-[0.18em] text-[#77766f]">
            Sentinel AI Guard
          </span>
        </div>
        <span
          className="grid size-8 place-items-center rounded-lg text-[#a5a39a]"
          aria-label="Protección activa"
          title="Protección activa"
        >
          <ShieldCheck className="size-[18px]" aria-hidden="true" />
        </span>
      </div>

      <nav className="px-3 pt-4" aria-label="Navegación principal">
        <p className="mb-2 px-3 text-[11px] font-medium uppercase tracking-[0.14em] text-[#6f6e68]">
          Espacio seguro
        </p>
        <div className="space-y-1">
          {NAVIGATION.map((item) => {
            const Icon = item.icon
            const link = (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    'flex h-11 items-center gap-3 rounded-xl px-3 text-[15px] text-[#c7c5bc] no-underline transition-colors hover:bg-white/[0.055] hover:text-[#f5f3ec] [&_svg]:size-[18px]',
                    isActive && 'bg-white/[0.075] text-[#faf9f5]',
                  )
                }
              >
                <Icon aria-hidden="true" />
                <span>{item.label}</span>
              </NavLink>
            )

            return mobile ? (
              <SheetClose key={item.to} asChild>
                {link}
              </SheetClose>
            ) : (
              link
            )
          })}
        </div>
      </nav>

      <div className="mt-8 px-6">
        <div className="h-px bg-white/[0.06]" />
        <p className="mt-5 text-xs leading-5 text-[#77766f]">
          Tus consultas se analizan antes de llegar al modelo local.
        </p>
      </div>

      <div className="mt-auto border-t border-white/[0.08] p-3">
        <UserProfileMenu />
      </div>
    </div>
  )
}
