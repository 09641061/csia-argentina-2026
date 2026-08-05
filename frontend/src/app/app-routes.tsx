import { Route, Routes } from 'react-router-dom'

import { LoginPage } from '@/contexts/iam/interfaces/login-page'
import { ProtectedRoute, PublicOnlyRoute } from '@/contexts/iam/interfaces/protected-route'
import { RegisterPage } from '@/contexts/iam/interfaces/register-page'
import { HistoryPage } from '@/contexts/analysis-and-decision/interfaces/history/history-page'
import { InteractionDetailPage } from '@/contexts/analysis-and-decision/interfaces/history/interaction-detail-page'
import { SecureQueryPage } from '@/contexts/analysis-and-decision/interfaces/secure-query/secure-query-page'

import { AppLayout } from './interfaces/app-layout'
import { NotFoundPage } from './interfaces/not-found-page'

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
