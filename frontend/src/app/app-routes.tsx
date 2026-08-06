import { Route, Routes } from 'react-router-dom'

import { LoginPage } from '@/contexts/iam/interfaces/login-page'
import { ProtectedRoute, PublicOnlyRoute } from '@/contexts/iam/interfaces/protected-route'
import { RegisterPage } from '@/contexts/iam/interfaces/register-page'
import { AnalysisDetailPage } from '@/contexts/analysis/interfaces/analysis-detail-page'
import { AnalysisPage } from '@/contexts/analysis/interfaces/analysis-page'
import { ChatPage } from '@/contexts/chat/interfaces/chat-page'
import { ChatsPage } from '@/contexts/chat/interfaces/chats-page'
import { AuditDetailPage } from '@/contexts/decision/interfaces/audit-detail-page'
import { AuditPage } from '@/contexts/decision/interfaces/audit-page'
import { SecureQueryPage } from '@/contexts/decision/interfaces/secure-query-page'

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
          <Route index element={<ChatPage />} />
          <Route path="chats" element={<ChatsPage />} />
          <Route path="chat/:conversationId" element={<ChatPage />} />
          <Route path="consulta-segura" element={<SecureQueryPage />} />
          <Route path="analisis" element={<AnalysisPage />} />
          <Route path="analisis/:analysisId" element={<AnalysisDetailPage />} />
          <Route path="auditoria" element={<AuditPage />} />
          <Route path="auditoria/:interactionId" element={<AuditDetailPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  )
}
