import { ChevronUp, LogOut, ShieldCheck, UserRound } from 'lucide-react'

import { useAuth } from '@/contexts/iam/interfaces/auth-context'
import { formatDateTime } from '@/shared/lib/format'
import { Avatar, AvatarFallback } from '@/shared/interfaces/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/interfaces/ui/dropdown-menu'

export function UserProfileMenu() {
  const { session, logout } = useAuth()
  const username = session?.username ?? 'Usuario local'
  const initials = username.slice(0, 2).toUpperCase()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className="group flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-left transition-colors hover:bg-white/[0.055] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#d97757]/60"
          aria-label="Abrir perfil de usuario"
        >
          <Avatar className="size-10 border border-white/10 bg-[#d8d5ca] text-[#1c1c1a]">
            <AvatarFallback className="bg-[#d8d5ca] text-sm font-medium text-[#1c1c1a]">
              {initials}
            </AvatarFallback>
          </Avatar>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-medium text-[#f3f1ea]">{username}</span>
            <span className="mt-0.5 block text-xs text-[#96958d]">Cuenta local</span>
          </span>
          <ChevronUp className="size-4 text-[#8d8c85] transition-transform group-aria-expanded:rotate-180" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        side="top"
        align="start"
        sideOffset={10}
        className="w-72 rounded-xl border border-white/10 bg-[#242422] p-2 text-[#f3f1ea] shadow-2xl"
      >
        <DropdownMenuLabel className="px-2 py-2 font-normal">
          <span className="flex items-center gap-2 text-[11px] uppercase tracking-[0.14em] text-[#96958d]">
            <UserRound className="size-3.5" /> Perfil
          </span>
          <span className="mt-2 block truncate text-sm font-medium text-[#f3f1ea]">{username}</span>
          <span className="mt-1 block text-xs leading-5 text-[#aaa89f]">
            Identidad validada por el endpoint IAM <code>/auth/me</code>.
          </span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator className="my-2 bg-white/10" />
        <DropdownMenuGroup>
          <div className="flex items-start gap-2 rounded-lg px-2 py-2 text-xs text-[#aaa89f]">
            <ShieldCheck className="mt-0.5 size-4 shrink-0 text-[#d97757]" />
            <span>
              Sesión protegida
              {session?.expiresAt && (
                <span className="mt-0.5 block text-[#7f7e77]">
                  Expira {formatDateTime(session.expiresAt)}
                </span>
              )}
            </span>
          </div>
        </DropdownMenuGroup>
        <DropdownMenuSeparator className="my-2 bg-white/10" />
        <DropdownMenuItem
          onSelect={logout}
          className="cursor-pointer gap-2 px-2 py-2 text-[#f3f1ea] focus:bg-white/[0.07] focus:text-white"
        >
          <LogOut className="size-4" aria-hidden="true" />
          Cerrar sesión
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
