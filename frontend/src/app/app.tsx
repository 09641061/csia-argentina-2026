import { BrowserRouter } from 'react-router-dom'

import { TooltipProvider } from '@/shared/interfaces/ui/tooltip'
import { AuthProvider } from '@/contexts/iam/interfaces/auth-provider'

import { AppRoutes } from './app-routes'

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <TooltipProvider>
          <AppRoutes />
        </TooltipProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
