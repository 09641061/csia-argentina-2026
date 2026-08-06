import { ArrowLeft, ArrowRight, FileKey2, FileSearch, MessageSquareText } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { ListAnalyses } from '@/contexts/analysis/application/list-analyses'
import { RunAnalysis } from '@/contexts/analysis/application/run-analysis'
import type { AnalysisPage as AnalysisPageModel, SecurityAnalysis } from '@/contexts/analysis/domain/security-analysis'
import { analysisStatusLabel, contentTypeLabel } from '@/contexts/analysis/domain/security-analysis'
import { HttpAnalysisRepository } from '@/contexts/analysis/infrastructure/http-analysis-repository'
import { apiErrorMessage } from '@/shared/infrastructure/api/api-error'
import { formatDateTime } from '@/shared/lib/format'
import { EmptyState } from '@/shared/interfaces/components/empty-state'
import { ErrorNotice } from '@/shared/interfaces/components/error-notice'
import { LoadingStatus } from '@/shared/interfaces/components/loading-status'
import { RiskLabel } from '@/shared/interfaces/components/risk-label'
import { Badge } from '@/shared/interfaces/ui/badge'
import { Button } from '@/shared/interfaces/ui/button'
import { Input } from '@/shared/interfaces/ui/input'
import { Spinner } from '@/shared/interfaces/ui/spinner'
import { Textarea } from '@/shared/interfaces/ui/textarea'
import { cn } from '@/shared/interfaces/utils'

export function AnalysisPage() {
  const repository = useMemo(() => new HttpAnalysisRepository(), [])
  const runAnalysis = useRef(new RunAnalysis(repository))
  const listAnalyses = useRef(new ListAnalyses(repository))
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedPage = Number.parseInt(searchParams.get('pagina') ?? '1', 10)
  const currentPage = Number.isInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1
  const [mode, setMode] = useState<'prompt' | 'document'>('prompt')
  const [prompt, setPrompt] = useState('')
  const [documentId, setDocumentId] = useState('')
  const [page, setPage] = useState<AnalysisPageModel | null>(null)
  const [result, setResult] = useState<SecurityAnalysis | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRunning, setIsRunning] = useState(false)
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

  const submit = async () => {
    setIsRunning(true)
    setErrorMessage(null)
    setResult(null)
    try {
      const analysis = await runAnalysis.current.execute(mode === 'prompt'
        ? { kind: 'prompt', prompt }
        : { kind: 'document', documentId: Number.parseInt(documentId, 10) })
      setResult(analysis)
      await load()
    } catch (error) {
      setErrorMessage(apiErrorMessage(error))
    } finally {
      setIsRunning(false)
    }
  }

  const totalPages = page ? Math.max(1, Math.ceil(page.total / page.pageSize)) : 1

  return (
    <div className="min-h-full bg-[#1b1b1a] px-5 pb-16 pt-24 text-[#f3f1ea] sm:px-8 lg:px-12">
      <section className="mx-auto w-full max-w-[1080px]">
        <header className="mb-8">
          <h1 className="page-heading">Análisis</h1>
          <p className="page-description">Revisa mensajes y documentos registrados sin exponer su contenido original.</p>
        </header>

        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <section className="claude-panel p-5 sm:p-6" aria-labelledby="new-analysis-title">
            <h2 id="new-analysis-title" className="text-base font-medium">Nueva revisión</h2>
            <div className="mt-5 flex rounded-xl bg-black/20 p-1">
              <ModeButton active={mode === 'prompt'} onClick={() => setMode('prompt')} icon={MessageSquareText}>Mensaje</ModeButton>
              <ModeButton active={mode === 'document'} onClick={() => setMode('document')} icon={FileKey2}>Documento registrado</ModeButton>
            </div>
            {mode === 'prompt' ? (
              <div className="mt-5">
                <label htmlFor="analysis-prompt" className="mb-2 block text-sm text-[#bbb9b1]">Contenido a revisar</label>
                <Textarea id="analysis-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} maxLength={8_000} rows={7} placeholder="Pega un mensaje para detectar información sensible…" className="resize-none border-white/10 bg-[#1c1c1b]" />
                <p className="mt-2 text-right text-xs text-[#77766f]">{prompt.length.toLocaleString('es')} / 8.000</p>
              </div>
            ) : (
              <div className="mt-5">
                <label htmlFor="document-id" className="mb-2 block text-sm text-[#bbb9b1]">ID del documento</label>
                <Input id="document-id" type="number" min="1" value={documentId} onChange={(event) => setDocumentId(event.target.value)} placeholder="Ej. 42" className="border-white/10 bg-[#1c1c1b]" />
                <p className="mt-3 text-xs leading-5 text-[#85847d]">Este endpoint analiza un documento que ya fue registrado por el backend.</p>
              </div>
            )}
            <Button className="mt-5 w-full rounded-xl bg-[#eceae3] text-[#222220] hover:bg-white" onClick={submit} disabled={isRunning || (mode === 'prompt' ? !prompt.trim() : !documentId)}>
              {isRunning ? <Spinner data-icon="inline-start" /> : <FileSearch data-icon="inline-start" />}
              {isRunning ? 'Analizando…' : 'Ejecutar análisis'}
            </Button>
          </section>

          <section className="claude-panel min-h-[360px] p-5 sm:p-6" aria-labelledby="analysis-result-title">
            <h2 id="analysis-result-title" className="text-base font-medium">Resultado más reciente</h2>
            {!result && !isRunning && <div className="grid min-h-[290px] place-items-center text-center text-sm text-[#85847d]"><div><FileSearch className="mx-auto mb-3 size-8" /><p>El nivel de riesgo, la explicación y los hallazgos<br />aparecerán aquí.</p></div></div>}
            {isRunning && <div className="mt-8"><LoadingStatus message="Revisando el contenido con los modelos locales…" /></div>}
            {result && !isRunning && <AnalysisSummary analysis={result} />}
          </section>
        </div>

        {errorMessage && <div className="mt-5"><ErrorNotice message={errorMessage} onRetry={mode === 'prompt' && prompt ? submit : load} /></div>}

        <section className="mt-10" aria-labelledby="analyses-history-title">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 id="analyses-history-title" className="font-serif text-2xl">Historial de análisis</h2>
            {page && <span className="text-sm text-[#85847d]">{page.total} ejecuciones</span>}
          </div>
          {isLoading && <LoadingStatus message="Cargando análisis…" />}
          {page && !isLoading && page.items.length === 0 && <EmptyState title="No hay análisis todavía" description="Ejecuta la primera revisión para ver su historial." />}
          {page && !isLoading && page.items.length > 0 && (
            <div className="overflow-hidden rounded-2xl border border-white/[0.08]">
              {page.items.map((analysis) => (
                <Link key={analysis.id} to={`/analisis/${analysis.id}`} className="flex flex-wrap items-center gap-3 border-b border-white/[0.07] px-4 py-4 text-[#efede6] no-underline transition last:border-0 hover:bg-white/[0.035] sm:px-5">
                  <span className="grid size-9 place-items-center rounded-lg bg-white/[0.055] text-[#aaa89f]">{analysis.contentType === 'prompt' ? <MessageSquareText className="size-[18px]" /> : <FileKey2 className="size-[18px]" />}</span>
                  <span className="min-w-0 flex-1"><span className="block truncate text-sm font-medium">{analysis.contentReference}</span><span className="mt-1 block text-xs text-[#85847d]">{contentTypeLabel(analysis.contentType)} · {formatDateTime(analysis.createdAt)}</span></span>
                  <Badge variant="outline" className="border-white/10 text-[#aaa89f]">{analysisStatusLabel(analysis.status)}</Badge>
                  <RiskLabel risk={analysis.riskLevel} />
                </Link>
              ))}
            </div>
          )}
          {page && page.total > page.pageSize && <div className="mt-4 flex justify-end gap-2"><Button variant="outline" disabled={currentPage === 1} onClick={() => setSearchParams(currentPage === 2 ? {} : { pagina: String(currentPage - 1) })}><ArrowLeft /> Anterior</Button><Button variant="outline" disabled={currentPage >= totalPages} onClick={() => setSearchParams({ pagina: String(currentPage + 1) })}>Siguiente <ArrowRight /></Button></div>}
        </section>
      </section>
    </div>
  )
}

function ModeButton({ active, onClick, icon: Icon, children }: { readonly active: boolean; readonly onClick: () => void; readonly icon: typeof MessageSquareText; readonly children: React.ReactNode }) {
  return <button type="button" onClick={onClick} className={cn('flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm transition', active ? 'bg-[#3a3a37] text-white shadow' : 'text-[#929088] hover:text-white')}><Icon className="size-4" />{children}</button>
}

function AnalysisSummary({ analysis }: { readonly analysis: SecurityAnalysis }) {
  return <div className="mt-6"><div className="flex flex-wrap items-center gap-2"><RiskLabel risk={analysis.riskLevel} /><Badge variant="outline" className="border-white/10 text-[#aaa89f]">{analysisStatusLabel(analysis.status)}</Badge></div><h3 className="mt-5 text-lg font-medium">{analysis.summary || 'Revisión completada'}</h3><p className="mt-3 text-sm leading-6 text-[#aaa89f]">{analysis.explanation || analysis.rationale || 'El análisis no devolvió una explicación.'}</p><dl className="mt-6 grid grid-cols-2 gap-4 text-sm"><div><dt className="text-xs text-[#77766f]">Hallazgos</dt><dd className="mt-1 font-medium">{analysis.findings.length}</dd></div><div><dt className="text-xs text-[#77766f]">Modelo</dt><dd className="mt-1 truncate font-medium">{analysis.modelName}</dd></div></dl><Button asChild variant="outline" className="mt-6 w-full"><Link to={`/analisis/${analysis.id}`}>Ver análisis completo</Link></Button></div>
}
