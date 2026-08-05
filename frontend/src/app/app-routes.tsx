import { Link, Route, Routes } from 'react-router-dom'

import { HistoryPage } from '@/modules/history/presentation/history-page'
import { InteractionDetailPage } from '@/modules/history/presentation/interaction-detail-page'
import { SecureQueryPage } from '@/modules/secure-query/presentation/secure-query-page'

import { AppLayout } from './app-layout'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<SecureQueryPage />} />
        <Route path="historial" element={<HistoryPage />} />
        <Route path="historial/:interactionId" element={<InteractionDetailPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}

function NotFoundPage() {
  return (
    <>
      <h1 className="page-title">Página no encontrada</h1>
      <p className="page-lead">La dirección que abriste no existe en Sentinel AI Guard.</p>
      <Link to="/">Ir a Consultar</Link>
    </>
  )
}
