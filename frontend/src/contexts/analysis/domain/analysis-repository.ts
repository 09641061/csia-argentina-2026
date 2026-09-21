import type { AnalysisFinding, AnalysisPage, SecurityAnalysis } from './security-analysis'

export interface AnalysisRepository {
  analyzePrompt(prompt: string, signal?: AbortSignal): Promise<SecurityAnalysis>
  analyzeDocument(documentId: number, signal?: AbortSignal): Promise<SecurityAnalysis>
  list(page: number, pageSize: number, signal?: AbortSignal): Promise<AnalysisPage>
  findById(analysisId: number, signal?: AbortSignal): Promise<SecurityAnalysis>
  listFindings(analysisId: number, signal?: AbortSignal): Promise<readonly AnalysisFinding[]>
}

