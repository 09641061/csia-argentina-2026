import { ArrowLeft, ExternalLink, ShieldAlert } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { GetInteraction } from '@/contexts/decision/application/get-interaction'
import type { SecureInteraction } from '@/contexts/decision/domain/secure-interaction'
import { decisionLabel, generationStatusLabel, interactionContentLabel } from '@/contexts/decision/domain/secure-interaction'
import { HttpDecisionRepository } from '@/contexts/decision/infrastructure/http-decision-repository'
import { apiErrorMessage } from '@/shared/infrastructure/api/api-error'
import { formatDateTime } from '@/shared/lib/format'
import { ErrorNotice } from '@/shared/interfaces/components/error-notice'
import { FindingsList } from '@/shared/interfaces/components/findings-list'
import { LoadingStatus } from '@/shared/interfaces/components/loading-status'
import { RiskLabel } from '@/shared/interfaces/components/risk-label'
import { Alert, AlertDescription } from '@/shared/interfaces/ui/alert'
import { Badge } from '@/shared/interfaces/ui/badge'
import { Button } from '@/shared/interfaces/ui/button'

export function AuditDetailPage() {
  const repository = useMemo(() => new HttpDecisionRepository(), [])
  const useCase = useRef(new GetInteraction(repository))
  const id = Number.parseInt(useParams().interactionId ?? '', 10)
  const [interaction, setInteraction] = useState<SecureInteraction | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [token, setToken] = useState(0)
  useEffect(() => { const controller = new AbortController(); setInteraction(null); setError(null); useCase.current.execute(id, controller.signal).then((value) => { if (!controller.signal.aborted) setInteraction(value) }).catch((caught) => { if (!controller.signal.aborted) setError(apiErrorMessage(caught)) }); return () => controller.abort() }, [id, token])
  return <div className="min-h-full bg-[#1b1b1a] px-5 pb-16 pt-24 text-[#f3f1ea] sm:px-8 lg:px-12"><section className="mx-auto w-full max-w-[920px]"><Button asChild variant="ghost" className="-ml-3 mb-7 text-[#aaa89f]"><Link to="/auditoria"><ArrowLeft /> Volver a auditoría</Link></Button>{!interaction && !error && <LoadingStatus message="Cargando la decisión…" />}{error && <ErrorNotice message={error} onRetry={() => setToken((value) => value + 1)} />}{interaction && <InteractionDetail interaction={interaction} />}</section></div>
}

function InteractionDetail({ interaction }: { readonly interaction: SecureInteraction }) {
  return <><header><div className="flex gap-2"><Badge className={interaction.decision === 'allowed' ? 'bg-[#2d3931] text-[#aed2b6]' : 'bg-[#3b2925] text-[#eda08b]'}>{decisionLabel(interaction.decision)}</Badge><RiskLabel risk={interaction.riskLevel} /></div><h1 className="page-heading mt-4">{interaction.contentReference}</h1><p className="page-description">{interaction.reason}</p></header>{interaction.decision === 'blocked' && <Alert className="mt-6 border-[#74433a]/60 bg-[#352522] text-[#f5c1b4]"><ShieldAlert /><AlertDescription>La generación se detuvo antes de que el contenido llegara al modelo de respuestas.</AlertDescription></Alert>}<section className="claude-panel mt-7 p-5 sm:p-6"><h2 className="text-base font-medium">Registro de decisión</h2><dl className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-3"><Detail label="ID" value={`#${interaction.id}`} /><Detail label="Tipo" value={interactionContentLabel(interaction.contentType)} /><Detail label="Fecha" value={formatDateTime(interaction.createdAt)} /><Detail label="Código de razón" value={interaction.reasonCode} /><Detail label="Generación" value={generationStatusLabel(interaction.generationStatus)} /><Detail label="Modelo" value={interaction.generationModel ?? 'No utilizado'} /></dl>{interaction.dataCategories.length > 0 && <div className="mt-6 flex flex-wrap gap-2">{interaction.dataCategories.map((category) => <Badge key={category} variant="outline">{category.replaceAll('_', ' ')}</Badge>)}</div>}</section>{interaction.maskedFindings.length > 0 && <section className="mt-8"><div className="mb-4 flex items-center justify-between"><h2 className="font-serif text-2xl">Hallazgos enmascarados</h2><span className="text-sm text-[#85847d]">{interaction.maskedFindings.length}</span></div><div className="claude-panel px-5"><FindingsList findings={interaction.maskedFindings} /></div></section>} {(interaction.promptAnalysisId || interaction.documentAnalysisId) && <section className="mt-8"><h2 className="mb-4 font-serif text-2xl">Análisis relacionados</h2><div className="flex flex-wrap gap-3">{interaction.promptAnalysisId && <Button asChild variant="outline"><Link to={`/analisis/${interaction.promptAnalysisId}`}>Análisis del mensaje <ExternalLink /></Link></Button>}{interaction.documentAnalysisId && <Button asChild variant="outline"><Link to={`/analisis/${interaction.documentAnalysisId}`}>Análisis del documento <ExternalLink /></Link></Button>}</div></section>}</>
}

function Detail({ label, value }: { readonly label: string; readonly value: string }) { return <div><dt className="text-xs text-[#77766f]">{label}</dt><dd className="mt-1 break-words text-sm font-medium">{value}</dd></div> }

