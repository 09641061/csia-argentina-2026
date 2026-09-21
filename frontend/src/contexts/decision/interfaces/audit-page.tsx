import { ArrowLeft, ArrowRight, Eye, ShieldCheck, ShieldX } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { ListInteractions } from '@/contexts/decision/application/list-interactions'
import type { InteractionPage } from '@/contexts/decision/domain/secure-interaction'
import { decisionLabel, generationStatusLabel, interactionContentLabel } from '@/contexts/decision/domain/secure-interaction'
import { HttpDecisionRepository } from '@/contexts/decision/infrastructure/http-decision-repository'
import { apiErrorMessage } from '@/shared/infrastructure/api/api-error'
import { formatDateTime } from '@/shared/lib/format'
import { EmptyState } from '@/shared/interfaces/components/empty-state'
import { ErrorNotice } from '@/shared/interfaces/components/error-notice'
import { LoadingStatus } from '@/shared/interfaces/components/loading-status'
import { RiskLabel } from '@/shared/interfaces/components/risk-label'
import { Badge } from '@/shared/interfaces/ui/badge'
import { Button } from '@/shared/interfaces/ui/button'

export function AuditPage() {
  const repository = useMemo(() => new HttpDecisionRepository(), [])
  const useCase = useRef(new ListInteractions(repository))
  const [params, setParams] = useSearchParams()
  const currentPage = Math.max(1, Number.parseInt(params.get('pagina') ?? '1', 10) || 1)
  const [page, setPage] = useState<InteractionPage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [token, setToken] = useState(0)

  useEffect(() => {
    const controller = new AbortController(); setPage(null); setError(null)
    useCase.current.execute(currentPage, controller.signal).then((value) => { if (!controller.signal.aborted) setPage(value) }).catch((caught) => { if (!controller.signal.aborted) setError(apiErrorMessage(caught)) })
    return () => controller.abort()
  }, [currentPage, token])

  const totalPages = page ? Math.max(1, Math.ceil(page.total / page.pageSize)) : 1
  return <div className="min-h-full bg-[#1b1b1a] px-5 pb-16 pt-24 text-[#f3f1ea] sm:px-8 lg:px-12"><section className="mx-auto w-full max-w-[1080px]"><header className="mb-8 flex flex-wrap items-end justify-between gap-4"><div><h1 className="page-heading">Auditoría</h1><p className="page-description">Decisiones de seguridad explicables, con evidencia siempre enmascarada.</p></div>{page && <Badge variant="outline">{page.total} interacciones</Badge>}</header>{!page && !error && <LoadingStatus message="Cargando auditoría…" />}{error && <ErrorNotice message={error} onRetry={() => setToken((value) => value + 1)} />}{page && page.items.length === 0 && <EmptyState title="No hay decisiones registradas" description="Las consultas seguras aparecerán aquí cuando se procesen." />}{page && page.items.length > 0 && <div className="overflow-hidden rounded-2xl border border-white/[0.08]">{page.items.map((item) => <Link key={item.id} to={`/auditoria/${item.id}`} className="group grid gap-3 border-b border-white/[0.07] px-4 py-4 text-[#efede6] no-underline transition last:border-0 hover:bg-white/[0.035] sm:grid-cols-[auto_1fr_auto_auto_auto] sm:items-center sm:px-5"><span className={`grid size-9 place-items-center rounded-lg ${item.decision === 'allowed' ? 'bg-[#29352e] text-[#a7cfb0]' : 'bg-[#3c2925] text-[#ef9d87]'}`}>{item.decision === 'allowed' ? <ShieldCheck className="size-[18px]" /> : <ShieldX className="size-[18px]" />}</span><span className="min-w-0"><span className="block truncate text-sm font-medium">{item.contentReference}</span><span className="mt-1 block text-xs text-[#85847d]">{interactionContentLabel(item.contentType)} · {formatDateTime(item.createdAt)}</span></span><RiskLabel risk={item.riskLevel} /><Badge className={item.decision === 'allowed' ? 'bg-[#2d3931] text-[#aed2b6]' : 'bg-[#3b2925] text-[#eda08b]'}>{decisionLabel(item.decision)}</Badge><span className="flex items-center gap-2 text-xs text-[#85847d]">{generationStatusLabel(item.generationStatus)}<Eye className="size-4 opacity-0 transition group-hover:opacity-100" /></span></Link>)}</div>}{page && page.total > page.pageSize && <div className="mt-4 flex justify-end gap-2"><Button variant="outline" disabled={currentPage === 1} onClick={() => setParams(currentPage === 2 ? {} : { pagina: String(currentPage - 1) })}><ArrowLeft /> Anterior</Button><Button variant="outline" disabled={currentPage >= totalPages} onClick={() => setParams({ pagina: String(currentPage + 1) })}>Siguiente <ArrowRight /></Button></div>}</section></div>
}

