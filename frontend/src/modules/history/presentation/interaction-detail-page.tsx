import { useMemo } from 'react'
import { Link, useParams } from 'react-router-dom'

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
    <>
      <Link className="back-link" to="/historial">
        ← Volver al historial
      </Link>

      {isLoading && <LoadingStatus message="Cargando la consulta…" />}
      {errorMessage && !isLoading && <ErrorNotice message={errorMessage} onRetry={retry} />}

      {detail && !isLoading && (
        <>
          <h1 className="page-title">{decisionLabel(detail.interaction.decision)}</h1>
          <p className="page-lead">{detail.interaction.reason}</p>

          <dl className="detail-list">
            <dt>Identificador</dt>
            <dd>#{detail.interaction.id}</dd>
            <dt>Tipo</dt>
            <dd>{contentTypeLabel(detail.interaction.contentType)}</dd>
            <dt>Referencia</dt>
            <dd>{detail.interaction.contentReference}</dd>
            <dt>Fecha</dt>
            <dd>{formatDateTime(detail.interaction.createdAt)}</dd>
            <dt>Riesgo</dt>
            <dd>
              <RiskLabel risk={detail.interaction.riskLevel} />
            </dd>
            <dt>Generación</dt>
            <dd>
              {generationStatusLabel(detail.interaction.generationStatus)}
              {detail.interaction.generationModel ? ` · ${detail.interaction.generationModel}` : ''}
              {detail.interaction.generationError ? ` · ${detail.interaction.generationError}` : ''}
            </dd>
          </dl>

          {detail.interaction.decision === 'blocked' && (
            <p className="section">
              El contenido no se envió al generador de respuestas de la IA.
            </p>
          )}

          {detail.interaction.maskedFindings.length > 0 && (
            <>
              <div className="section">
                <h2 className="section__title">Información detectada</h2>
                <div className="detected-types">
                  {detectedInformationTypes(detail.interaction.maskedFindings).map((type) => (
                    <span className="tag" key={type}>
                      {type}
                    </span>
                  ))}
                </div>
              </div>

              <div className="section">
                <h2 className="section__title">Hallazgos enmascarados</h2>
                <FindingsList findings={detail.interaction.maskedFindings} />
              </div>
            </>
          )}

          <div className="section">
            <h2 className="section__title">Revisiones realizadas</h2>
            {detail.promptAnalysis === null && detail.documentAnalysis === null && (
              <p>No hay revisiones asociadas disponibles.</p>
            )}
            {detail.promptAnalysis && (
              <ReviewSummary title="Consulta" analysis={detail.promptAnalysis} />
            )}
            {detail.documentAnalysis && (
              <ReviewSummary title="Documento" analysis={detail.documentAnalysis} />
            )}
          </div>
        </>
      )}
    </>
  )
}

interface ReviewSummaryProps {
  readonly title: string
  readonly analysis: SecurityAnalysis
}

function ReviewSummary({ title, analysis }: ReviewSummaryProps) {
  return (
    <section className="review">
      <p className="review__head">
        <span className="review__title">{title}</span>
        <RiskLabel risk={analysis.riskLevel} />
        <span className="table__date">{analysisStatusLabel(analysis.status)}</span>
        <span className="table__date">Modelo {analysis.modelName}</span>
      </p>
      <p className="review__body">{analysis.explanation}</p>
      {analysis.maskedPreview && (
        <p className="review__preview">Vista previa enmascarada: {analysis.maskedPreview}</p>
      )}
      {analysis.contentTruncated && (
        <p className="review__body">
          El contenido era mayor que el contexto analizado y se resumió de forma segura.
        </p>
      )}
    </section>
  )
}
