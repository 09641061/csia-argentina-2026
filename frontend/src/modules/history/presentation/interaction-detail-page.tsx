import { ArrowLeft, FileSearch, ShieldAlert } from 'lucide-react'
import { useMemo } from 'react'
import { Link, useParams } from 'react-router-dom'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { analysisStatusLabel } from '@/modules/analysis/domain/analysis-status'
import { contentTypeLabel } from '@/modules/analysis/domain/content-type'
import { decisionLabel } from '@/modules/analysis/domain/decision'
import { detectedInformationTypes } from '@/modules/analysis/domain/finding'
import { generationStatusLabel } from '@/modules/analysis/domain/generation-status'
import type { SecurityAnalysis } from '@/modules/analysis/domain/security-analysis'
import { HttpInteractionRepository } from '@/modules/history/infrastructure/http-interaction-repository'
import { formatDateTime } from '@/shared/lib/format'
import { ErrorNotice } from '@/shared/ui/error-notice'
import { FindingsList } from '@/shared/ui/findings-list'
import { LoadingStatus } from '@/shared/ui/loading-status'
import { RiskLabel } from '@/shared/ui/risk-label'

import { useInteractionDetail } from './use-interaction-detail'

export function InteractionDetailPage() {
  const repository = useMemo(() => new HttpInteractionRepository(), [])
  const { interactionId } = useParams()
  const parsedId = Number.parseInt(interactionId ?? '', 10)
  const { detail, isLoading, errorMessage, retry } = useInteractionDetail(repository, parsedId)

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <Button asChild variant="ghost" className="-ml-2 self-start">
        <Link to="/historial">
          <ArrowLeft data-icon="inline-start" /> Volver al historial
        </Link>
      </Button>

      {isLoading && <LoadingStatus message="Cargando la consulta…" />}
      {errorMessage && !isLoading && <ErrorNotice message={errorMessage} onRetry={retry} />}

      {detail && !isLoading && (
        <>
          <header>
            <p className="mb-2 text-sm font-medium text-muted-foreground">
              Interacción #{detail.interaction.id}
            </p>
            <h1 className="page-heading">{decisionLabel(detail.interaction.decision)}</h1>
            <p className="page-description">{detail.interaction.reason}</p>
          </header>

          <section aria-labelledby="audit-summary-title" className="flex flex-col gap-5">
            <h2 id="audit-summary-title" className="text-base font-semibold">
              Resumen de auditoría
            </h2>
            <dl className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              <Detail label="Tipo" value={contentTypeLabel(detail.interaction.contentType)} />
              <Detail label="Referencia" value={detail.interaction.contentReference} />
              <Detail label="Fecha" value={formatDateTime(detail.interaction.createdAt)} />
              <div>
                <dt className="text-xs font-medium text-muted-foreground">Riesgo</dt>
                <dd className="mt-1">
                  <RiskLabel risk={detail.interaction.riskLevel} />
                </dd>
              </div>
              <Detail
                label="Generación"
                value={generationStatusLabel(detail.interaction.generationStatus)}
              />
              <Detail label="Modelo" value={detail.interaction.generationModel ?? 'No utilizado'} />
            </dl>
            {detail.interaction.generationError && (
              <p className="text-sm text-destructive">{detail.interaction.generationError}</p>
            )}
          </section>

          {detail.interaction.decision === 'blocked' && (
            <Alert variant="destructive">
              <ShieldAlert aria-hidden="true" />
              <AlertDescription>
                El contenido no se envió al generador de respuestas de la IA.
              </AlertDescription>
            </Alert>
          )}

          {detail.interaction.maskedFindings.length > 0 && (
            <>
              <Separator />
              <section className="flex flex-col gap-4" aria-labelledby="masked-findings-title">
                <h2 id="masked-findings-title" className="text-base font-semibold">
                  Hallazgos enmascarados
                </h2>
                <div className="flex flex-wrap gap-2">
                  {detectedInformationTypes(detail.interaction.maskedFindings).map((type) => (
                    <Badge variant="secondary" key={type}>
                      {type}
                    </Badge>
                  ))}
                </div>
                <FindingsList findings={detail.interaction.maskedFindings} />
              </section>
            </>
          )}

          <Separator />
          <section className="flex flex-col gap-4" aria-labelledby="reviews-title">
            <h2
              id="reviews-title"
              className="flex items-center gap-2 text-base font-semibold [&_svg]:size-4"
            >
              <FileSearch aria-hidden="true" /> Revisiones realizadas
            </h2>
            {detail.promptAnalysis === null && detail.documentAnalysis === null && (
              <p className="text-sm text-muted-foreground">
                No hay revisiones asociadas disponibles.
              </p>
            )}
            {detail.promptAnalysis && (
              <ReviewSummary title="Consulta" analysis={detail.promptAnalysis} />
            )}
            {detail.documentAnalysis && (
              <ReviewSummary title="Documento" analysis={detail.documentAnalysis} />
            )}
          </section>
        </>
      )}
    </div>
  )
}

function Detail({ label, value }: { readonly label: string; readonly value: string }) {
  return (
    <div>
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-1 break-words text-sm font-medium">{value}</dd>
    </div>
  )
}

function ReviewSummary({
  title,
  analysis,
}: {
  readonly title: string
  readonly analysis: SecurityAnalysis
}) {
  return (
    <article className="flex flex-col gap-3 border-l-2 pl-4">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-medium">{title}</h3>
        <RiskLabel risk={analysis.riskLevel} />
        <Badge variant="outline">{analysisStatusLabel(analysis.status)}</Badge>
        <Badge variant="outline">{analysis.modelName}</Badge>
      </div>
      <p className="text-sm leading-6 text-muted-foreground">{analysis.explanation}</p>
      {analysis.maskedPreview && (
        <p className="rounded-lg bg-muted p-3 font-mono text-xs break-words">
          Vista previa enmascarada: {analysis.maskedPreview}
        </p>
      )}
      {analysis.contentTruncated && (
        <p className="text-xs text-muted-foreground">
          El contenido era mayor que el contexto analizado y se resumió de forma segura.
        </p>
      )}
    </article>
  )
}
