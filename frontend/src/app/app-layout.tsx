import { Clock3, LogOut, Menu, MessageSquareText, ShieldCheck, UserRound } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { cn } from '@/lib/utils'
import { useAuth } from '@/modules/auth/presentation/auth-provider'

const NAVIGATION = [
  { to: '/', label: 'Consultar', end: true, icon: MessageSquareText },
  { to: '/historial', label: 'Historial', end: false, icon: Clock3 },
]

export function AppLayout() {
  const { session, logout } = useAuth()

  return (
    <div className="min-h-svh bg-background">
      <header className="sticky top-0 z-40 border-b bg-background">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
          <NavLink className="flex min-w-0 items-center gap-2.5 text-foreground no-underline" to="/">
            <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-primary text-primary-foreground [&_svg]:size-5">
              <ShieldCheck aria-hidden="true" />
            </span>
            <span className="hidden text-sm font-semibold tracking-tight sm:block">
              Sentinel AI Guard
            </span>
          </NavLink>

          <nav className="ml-4 hidden items-center gap-1 md:flex" aria-label="Navegación principal">
            <NavigationLinks />
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="lg" className="px-2" aria-label="Menú de usuario">
                  <Avatar size="sm">
                    <AvatarFallback className="text-xs font-semibold">
                      {session?.username.slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden max-w-36 truncate text-sm sm:block">{session?.username}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuGroup>
                  <DropdownMenuLabel className="font-normal">
                    <span className="block text-xs text-muted-foreground">Usuario</span>
                    <span className="block truncate text-sm font-medium">{session?.username}</span>
                  </DropdownMenuLabel>
                </DropdownMenuGroup>
                <DropdownMenuSeparator />
                <DropdownMenuGroup>
                  <DropdownMenuItem onClick={logout}>
                    <LogOut aria-hidden="true" />
                    Cerrar sesión
                  </DropdownMenuItem>
                </DropdownMenuGroup>
              </DropdownMenuContent>
            </DropdownMenu>

            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" size="icon" className="md:hidden" aria-label="Abrir menú">
                  <Menu aria-hidden="true" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-72">
                <SheetHeader>
                  <SheetTitle className="flex items-center gap-2">
                    <ShieldCheck /> Sentinel
                  </SheetTitle>
                </SheetHeader>
                <nav className="grid gap-1 px-4" aria-label="Navegación móvil">
                  <NavigationLinks mobile />
                </nav>
                <div className="mt-auto">
                  <Separator />
                  <p className="flex items-center gap-2 p-4 text-sm text-muted-foreground [&_svg]:size-4">
                    <UserRound aria-hidden="true" /> {session?.username}
                  </p>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
        <Outlet />
      </main>
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
        className={({ isActive }) =>
          cn(
            'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground no-underline transition-colors hover:bg-muted hover:text-foreground [&_svg]:size-4',
            isActive && 'bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground',
            mobile && 'w-full py-2.5',
          )
        }
      >
        <Icon aria-hidden="true" />
        {item.label}
      </NavLink>
    )
  })
}
