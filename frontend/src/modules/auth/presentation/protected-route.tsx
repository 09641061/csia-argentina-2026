import { LoaderCircle } from 'lucide-react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '@/modules/auth/presentation/auth-provider'

export function ProtectedRoute() {
  const { session, isCheckingSession } = useAuth()
  const location = useLocation()

  if (isCheckingSession) {
    return (
      <div className="grid min-h-svh place-items-center bg-muted/30">
        <div className="flex items-center gap-2 text-sm text-muted-foreground" role="status">
          <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />
          Verificando sesión segura…
        </div>
      </div>
    )
  }

  if (!session) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}

export function PublicOnlyRoute() {
  const { session, isCheckingSession } = useAuth()
  if (isCheckingSession) return null
  if (session) return <Navigate to="/" replace />
  return <Outlet />
}
