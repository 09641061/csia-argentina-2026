import { ShieldCheck } from 'lucide-react'
import { Outlet } from 'react-router-dom'

import {
  AppSidebar,
  MobileSidebar,
} from '@/contexts/analysis-and-decision/interfaces/layout/app-sidebar'

export function AppLayout() {
  return (
    <div className="flex h-svh overflow-hidden bg-[#1b1b1a] text-[#f3f1ea]">
      <AppSidebar />

      <div className="relative flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="pointer-events-none absolute inset-x-0 top-0 z-40 flex h-16 items-center justify-between px-3 sm:px-5">
          <div className="pointer-events-auto">
            <MobileSidebar />
          </div>
          <div className="absolute left-1/2 top-3 -translate-x-1/2 rounded-xl border border-white/[0.055] bg-[#111110]/90 px-3 py-2 text-xs text-[#aaa89f] shadow-lg backdrop-blur">
            <span>Protección local</span>
            <span className="mx-2 text-[#55544f]">•</span>
            <span className="text-[#d7a28f]">Activa</span>
          </div>
          <span
            className="grid size-9 place-items-center rounded-lg text-[#9b9a92]"
            title="Sentinel AI Guard"
            aria-label="Sentinel AI Guard"
          >
            <ShieldCheck className="size-[19px]" aria-hidden="true" />
          </span>
        </header>

        <main className="min-h-0 flex-1 overflow-y-auto" id="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
