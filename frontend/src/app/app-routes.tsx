import { Link, Route, Routes } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { LoginPage } from '@/modules/auth/presentation/login-page'
import { ProtectedRoute, PublicOnlyRoute } from '@/modules/auth/presentation/protected-route'
import { RegisterPage } from '@/modules/auth/presentation/register-page'
import { HistoryPage } from '@/modules/history/presentation/history-page'
import { InteractionDetailPage } from '@/modules/history/presentation/interaction-detail-page'
import { SecureQueryPage } from '@/modules/secure-query/presentation/secure-query-page'

import { AppLayout } from './app-layout'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<SecureQueryPage />} />
          <Route path="historial" element={<HistoryPage />} />
          <Route path="historial/:interactionId" element={<InteractionDetailPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  )
}

function NotFoundPage() {
  return (
    <section className="mx-auto flex min-h-[60vh] max-w-lg flex-col items-center justify-center text-center">
      <span className="text-sm font-medium text-muted-foreground">404</span>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight">Página no encontrada</h1>
      <p className="mt-3 text-muted-foreground">
        La dirección que abriste no existe en Sentinel AI Guard.
      </p>
      <Button asChild className="mt-6">
        <Link to="/">Ir a Consultar</Link>
      </Button>
    </section>
  )
}
