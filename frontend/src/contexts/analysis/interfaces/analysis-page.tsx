import { ArrowLeft, ArrowRight, MessageSquareText } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { ListAnalyses } from '@/contexts/analysis/application/list-analyses'
import type { AnalysisPage as AnalysisPageModel } from '@/contexts/analysis/domain/security-analysis'
import { analysisStatusLabel } from '@/contexts/analysis/domain/security-analysis'
import { HttpAnalysisRepository } from '@/contexts/analysis/infrastructure/http-analysis-repository'
import { apiErrorMessage } from '@/shared/infrastructure/api/api-error'
import { EmptyState } from '@/shared/interfaces/components/empty-state'
import { ErrorNotice } from '@/shared/interfaces/components/error-notice'
import { LoadingStatus } from '@/shared/interfaces/components/loading-status'
import { RiskLabel } from '@/shared/interfaces/components/risk-label'
import { Badge } from '@/shared/interfaces/ui/badge'
import { Button } from '@/shared/interfaces/ui/button'
import { formatDateTime } from '@/shared/lib/format'

export function AnalysisPage() {
  const repository = useMemo(() => new HttpAnalysisRepository(), [])
  const listAnalyses = useRef(new ListAnalyses(repository))
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedPage = Number.parseInt(searchParams.get('pagina') ?? '1', 10)
  const currentPage = Number.isInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1
  const [page, setPage] = useState<AnalysisPageModel | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      setPage(await listAnalyses.current.execute(currentPage))
    } catch (error) {
      setErrorMessage(apiErrorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }, [currentPage])

  useEffect(() => { void load() }, [load])

  const totalPages = page ? Math.max(1, Math.ceil(page.total / page.pageSize)) : 1

  return (
    <div className="min-h-full bg-[#1b1b1a] px-5 pb-16 pt-24 text-[#f3f1ea] sm:px-8 lg:px-12">
      <section className="mx-auto w-full max-w-[1080px]">
        <header className="mb-8">
          <h1 className="page-heading">Análisis</h1>
          <p className="page-description">Resultados de seguridad generados automáticamente al enviar mensajes en tus chats.</p>
        </header>

        {errorMessage && <div className="mb-5"><ErrorNotice message={errorMessage} onRetry={load} /></div>}
        {isLoading && <LoadingStatus message="Cargando análisis de los chats…" />}
        {page && !isLoading && page.items.length === 0 && (
          <EmptyState title="No hay análisis todavía" description="Envía un mensaje en un chat para generar el primer resultado de seguridad." />
        )}
        {page && !isLoading && page.items.length > 0 && (
          <div className="overflow-hidden rounded-2xl border border-white/[0.08]">
            {page.items.map((analysis) => (
              <Link key={analysis.id} to={`/analisis/${analysis.id}`} className="flex flex-wrap items-center gap-3 border-b border-white/[0.07] px-4 py-4 text-[#efede6] no-underline transition last:border-0 hover:bg-white/[0.035] sm:px-5">
                <span className="grid size-9 place-items-center rounded-lg bg-white/[0.055] text-[#aaa89f]"><MessageSquareText className="size-[18px]" /></span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium">{analysis.summary || analysis.contentReference}</span>
                  <span className="mt-1 block text-xs text-[#85847d]">Mensaje de chat · {formatDateTime(analysis.createdAt)}</span>
                </span>
                <Badge variant="outline" className="border-white/10 text-[#aaa89f]">{analysisStatusLabel(analysis.status)}</Badge>
                <RiskLabel risk={analysis.riskLevel} />
              </Link>
            ))}
          </div>
        )}
        {page && page.total > page.pageSize && (
          <div className="mt-4 flex justify-end gap-2">
            <Button variant="outline" disabled={currentPage === 1} onClick={() => setSearchParams(currentPage === 2 ? {} : { pagina: String(currentPage - 1) })}><ArrowLeft /> Anterior</Button>
            <Button variant="outline" disabled={currentPage >= totalPages} onClick={() => setSearchParams({ pagina: String(currentPage + 1) })}>Siguiente <ArrowRight /></Button>
          </div>
        )}
      </section>
    </div>
  )
}
