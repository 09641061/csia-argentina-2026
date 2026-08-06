import { ArrowLeft, Fingerprint, ShieldAlert } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { GetAnalysisDetail } from '@/contexts/analysis/application/get-analysis-detail'
import type { SecurityAnalysis } from '@/contexts/analysis/domain/security-analysis'
import { analysisStatusLabel, contentTypeLabel } from '@/contexts/analysis/domain/security-analysis'
import { HttpAnalysisRepository } from '@/contexts/analysis/infrastructure/http-analysis-repository'
import { apiErrorMessage } from '@/shared/infrastructure/api/api-error'
import { formatDateTime } from '@/shared/lib/format'
import { ErrorNotice } from '@/shared/interfaces/components/error-notice'
import { FindingsList } from '@/shared/interfaces/components/findings-list'
import { LoadingStatus } from '@/shared/interfaces/components/loading-status'
import { RiskLabel } from '@/shared/interfaces/components/risk-label'
import { Alert, AlertDescription, AlertTitle } from '@/shared/interfaces/ui/alert'
import { Badge } from '@/shared/interfaces/ui/badge'
import { Button } from '@/shared/interfaces/ui/button'

export function AnalysisDetailPage() {
  const repository = useMemo(() => new HttpAnalysisRepository(), [])
  const useCase = useRef(new GetAnalysisDetail(repository))
  const id = Number.parseInt(useParams().analysisId ?? '', 10)
  const [analysis, setAnalysis] = useState<SecurityAnalysis | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [token, setToken] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setAnalysis(null); setError(null)
    useCase.current.execute(id, controller.signal).then(({ analysis: value }) => { if (!controller.signal.aborted) setAnalysis(value) }).catch((caught) => { if (!controller.signal.aborted) setError(apiErrorMessage(caught)) })
    return () => controller.abort()
  }, [id, token])

  return <div className="min-h-full bg-[#1b1b1a] px-5 pb-16 pt-24 text-[#f3f1ea] sm:px-8 lg:px-12"><section className="mx-auto w-full max-w-[920px]"><Button asChild variant="ghost" className="-ml-3 mb-7 text-[#aaa89f]"><Link to="/analisis"><ArrowLeft /> Volver a análisis</Link></Button>{!analysis && !error && <LoadingStatus message="Cargando el análisis…" />}{error && <ErrorNotice message={error} onRetry={() => setToken((value) => value + 1)} />}{analysis && <AnalysisDetail analysis={analysis} />}</section></div>
}

function AnalysisDetail({ analysis }: { readonly analysis: SecurityAnalysis }) {
  return <><header><div className="flex flex-wrap items-center gap-2"><RiskLabel risk={analysis.riskLevel} /><Badge variant="outline">{analysisStatusLabel(analysis.status)}</Badge><Badge variant="outline">{contentTypeLabel(analysis.contentType)}</Badge></div><h1 className="page-heading mt-4">{analysis.summary || `Análisis #${analysis.id}`}</h1><p className="page-description">{analysis.explanation || analysis.rationale}</p></header>{analysis.tamperingSuspected && <Alert className="mt-6 border-[#7e4a3f] bg-[#3b2925]"><ShieldAlert /><AlertTitle>Manipulación sospechada</AlertTitle><AlertDescription>El modelo detectó señales que requieren revisión adicional.</AlertDescription></Alert>}<section className="claude-panel mt-7 p-5 sm:p-6"><h2 className="text-base font-medium">Resumen técnico</h2><dl className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-3"><Detail label="Referencia" value={analysis.contentReference} /><Detail label="Modelo" value={analysis.modelName} /><Detail label="Fecha" value={formatDateTime(analysis.analyzedAt ?? analysis.createdAt)} /><Detail label="Longitud" value={`${analysis.contentLength.toLocaleString('es')} caracteres`} /><Detail label="Confianza" value={analysis.confidence ?? 'No disponible'} /><Detail label="Sujetos estimados" value={analysis.estimatedSubjects} /></dl>{analysis.maskedPreview && <div className="mt-6"><p className="flex items-center gap-2 text-xs text-[#85847d]"><Fingerprint className="size-4" /> Vista previa enmascarada</p><pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded-xl bg-black/20 p-4 text-xs leading-6 text-[#c9c7bf]">{analysis.maskedPreview}</pre></div>}</section><section className="mt-8"><div className="mb-4 flex items-center justify-between"><h2 className="font-serif text-2xl">Hallazgos</h2><span className="text-sm text-[#85847d]">{analysis.findings.length}</span></div>{analysis.findings.length ? <div className="claude-panel px-5"><FindingsList findings={analysis.findings} /></div> : <p className="rounded-2xl border border-white/[0.08] p-6 text-sm text-[#aaa89f]">No se detectó información sensible.</p>}</section></>
}

function Detail({ label, value }: { readonly label: string; readonly value: string }) { return <div><dt className="text-xs text-[#77766f]">{label}</dt><dd className="mt-1 break-words text-sm font-medium">{value || 'No disponible'}</dd></div> }

