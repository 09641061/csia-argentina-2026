import type { AnalysisRepository } from '@/contexts/analysis/domain/analysis-repository'
import type { AnalysisFinding, AnalysisPage, SecurityAnalysis } from '@/contexts/analysis/domain/security-analysis'
import { request } from '@/shared/infrastructure/api/http-client'
import type { AnalysisFindingsResource, SecurityAnalysisListResource, SecurityAnalysisResource } from '@/shared/infrastructure/api/resources'

import { toAnalysisFinding, toSecurityAnalysis } from './analysis-mapper'

export class HttpAnalysisRepository implements AnalysisRepository {
  async analyzePrompt(prompt: string, signal?: AbortSignal): Promise<SecurityAnalysis> {
    const resource = await request<SecurityAnalysisResource>('/api/v1/prompts/analyses', {
      method: 'POST', body: { prompt }, signal,
    })
    return toSecurityAnalysis(resource)
  }

  async analyzeDocument(documentId: number, signal?: AbortSignal): Promise<SecurityAnalysis> {
    const resource = await request<SecurityAnalysisResource>(`/api/v1/documents/${documentId}/analyses`, {
      method: 'POST', signal,
    })
    return toSecurityAnalysis(resource)
  }

  async list(page: number, pageSize: number, signal?: AbortSignal): Promise<AnalysisPage> {
    const resource = await request<SecurityAnalysisListResource>(`/api/v1/analyses?page=${page}&page_size=${pageSize}`, { signal, timeoutMs: 20_000 })
    return { items: resource.items.map(toSecurityAnalysis), page: resource.page.page, pageSize: resource.page.page_size, total: resource.page.total }
  }

  async findById(analysisId: number, signal?: AbortSignal): Promise<SecurityAnalysis> {
    return toSecurityAnalysis(await request<SecurityAnalysisResource>(`/api/v1/analyses/${analysisId}`, { signal, timeoutMs: 20_000 }))
  }

  async listFindings(analysisId: number, signal?: AbortSignal): Promise<readonly AnalysisFinding[]> {
    const resource = await request<AnalysisFindingsResource>(`/api/v1/analyses/${analysisId}/findings`, { signal, timeoutMs: 20_000 })
    const analysis = await this.findById(analysisId, signal)
    return resource.items.map((finding) => toAnalysisFinding(finding, analysis.contentType))
  }
}

