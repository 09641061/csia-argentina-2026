import { Outlet } from 'react-router-dom'

import { AppSidebar, MobileSidebar } from '@/contexts/chat/interfaces/app-sidebar'
import { ChatProvider } from '@/contexts/chat/interfaces/chat-provider'

export function AppLayout() {
  return (
    <ChatProvider>
      <div className="flex h-svh overflow-hidden bg-[#1b1b1a] text-[#f3f1ea]">
        <AppSidebar />
        <div className="relative flex min-w-0 flex-1 flex-col overflow-hidden">
          <header className="pointer-events-none absolute inset-x-0 top-0 z-40 flex h-16 items-center px-3 sm:px-5">
            <div className="pointer-events-auto"><MobileSidebar /></div>
          </header>
          <main className="min-h-0 flex-1 overflow-y-auto" id="main-content"><Outlet /></main>
        </div>
      </div>
    </ChatProvider>
  )
}
