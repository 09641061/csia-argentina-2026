import { afterEach, describe, expect, it, vi } from 'vitest'

import { HttpAnalysisRepository } from '@/contexts/analysis/infrastructure/http-analysis-repository'
import { HttpChatRepository } from '@/contexts/chat/infrastructure/http-chat-repository'
import { HttpDecisionRepository } from '@/contexts/decision/infrastructure/http-decision-repository'
import { HttpAuthRepository } from '@/contexts/iam/infrastructure/http-auth-repository'
import { getSystemHealth } from '@/shared/infrastructure/api/http-health-service'
import { allowedInteractionResource, analysisResource, secureQueryResponse } from '@/test/builders'

afterEach(() => vi.unstubAllGlobals())

describe('Cobertura del contrato REST del backend', () => {
  it('connects every current backend endpoint to a frontend repository', async () => {
    const calls = new Set<string>()
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = new URL(input.toString())
      const method = init?.method ?? 'GET'
      const key = `${method} ${url.pathname}`
      calls.add(key)

      const now = '2026-08-05T12:00:00Z'
      const responses: Record<string, unknown> = {
        'POST /api/v1/auth/login': { access_token: 'jwt', token_type: 'bearer', expires_at: now, username: 'demo' },
        'POST /api/v1/auth/register': { access_token: 'jwt', token_type: 'bearer', expires_at: now, username: 'demo' },
        'GET /api/v1/auth/me': { username: 'demo' },
        'GET /api/v1/health': {
          status: 'ok', database: true,
          security_model_available: true, discovery_model_available: true,
          generation_model_available: true, vision_model_available: true,
          security_model: 'security', discovery_model: 'discovery', generation_model: 'generation', vision_model: 'vision',
        },
        'GET /api/v1/chat/conversations': [{ id: 1, title: 'Arquitectura DDD', created_at: now, updated_at: now }],
        'GET /api/v1/chat/conversations/1': { id: 1, title: 'Arquitectura DDD', created_at: now, updated_at: now, messages: [{ id: 1, role: 'user', content: 'Hola', created_at: now }] },
        'POST /api/v1/chat/conversations': { conversation_id: 1, answer: 'Respuesta', model_name: 'local', generated_at: now },
        'POST /api/v1/chat/conversations/1/messages': { conversation_id: 1, answer: 'Respuesta', model_name: 'local', generated_at: now },
        'POST /api/v1/prompts/analyses': analysisResource(),
        'POST /api/v1/documents/1/analyses': analysisResource({ content_type: 'document', document_id: 1 }),
        'GET /api/v1/analyses': { items: [analysisResource()], page: { page: 1, page_size: 12, total: 1 } },
        'GET /api/v1/analyses/10': analysisResource(),
        'GET /api/v1/analyses/10/findings': { analysis_id: 10, items: [] },
        'POST /api/v1/secure-queries': secureQueryResponse(allowedInteractionResource()),
        'GET /api/v1/interactions': { items: [allowedInteractionResource()], page: { page: 1, page_size: 15, total: 1 } },
        'GET /api/v1/interactions/1': allowedInteractionResource(),
      }
      const body = responses[key]
      return new Response(JSON.stringify(body ?? { detail: `Unmocked ${key}` }), {
        status: body === undefined ? 404 : method === 'POST' ? 201 : 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }))

    const auth = new HttpAuthRepository()
    await auth.login('demo', 'password')
    await auth.register('demo', 'password')
    await auth.currentUser()
    await getSystemHealth()

    const chat = new HttpChatRepository()
    await chat.list()
    await chat.findById(1)
    await chat.create('Hola')
    await chat.send(1, 'Continúa')

    const analysis = new HttpAnalysisRepository()
    await analysis.analyzePrompt('Revisa esto')
    await analysis.analyzeDocument(1)
    await analysis.list(1, 12)
    await analysis.findById(10)
    await analysis.listFindings(10)

    const decision = new HttpDecisionRepository()
    await decision.submit({ prompt: 'Consulta segura', file: null })
    await decision.list(1, 15)
    await decision.findById(1)

    expect(calls).toEqual(new Set([
      'GET /api/v1/health',
      'POST /api/v1/auth/login',
      'POST /api/v1/auth/register',
      'GET /api/v1/auth/me',
      'GET /api/v1/chat/conversations',
      'POST /api/v1/chat/conversations',
      'GET /api/v1/chat/conversations/1',
      'POST /api/v1/chat/conversations/1/messages',
      'POST /api/v1/prompts/analyses',
      'POST /api/v1/documents/1/analyses',
      'GET /api/v1/analyses',
      'GET /api/v1/analyses/10',
      'GET /api/v1/analyses/10/findings',
      'POST /api/v1/secure-queries',
      'GET /api/v1/interactions',
      'GET /api/v1/interactions/1',
    ]))
  })
})

