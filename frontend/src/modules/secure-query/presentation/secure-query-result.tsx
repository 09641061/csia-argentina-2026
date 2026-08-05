import { Link } from 'react-router-dom'

import { includesPrompt } from '@/modules/analysis/domain/content-type'
import { decisionLabel } from '@/modules/analysis/domain/decision'
import { detectedInformationTypes } from '@/modules/analysis/domain/finding'
import type { AssistantResponse } from '@/modules/secure-query/domain/assistant-response'
import {
  passedReviewButHasNoAnswer,
  wasAllowed,
  type SecureInteraction,
} from '@/modules/secure-query/domain/secure-interaction'
import { FindingsList } from '@/shared/ui/findings-list'
import { RiskLabel } from '@/shared/ui/risk-label'
import { formatDateTime } from '@/shared/lib/format'

interface SecureQueryResultProps {
  readonly interaction: SecureInteraction
  readonly answer: AssistantResponse | null
  readonly onNewQuery: () => void
}

export function SecureQueryResult({ interaction, answer, onNewQuery }: SecureQueryResultProps) {
  const allowed = wasAllowed(interaction)
  const askedSomething = includesPrompt(interaction.contentType)
  const detectedTypes = detectedInformationTypes(interaction.maskedFindings)

  return (
    <section
      className={`result result--${interaction.decision}`}
      aria-live="polite"
      data-testid="secure-query-result"
    >
      <h2 className="result__verdict">
        {allowed && !askedSomething ? 'Documento permitido' : decisionLabel(interaction.decision)}
      </h2>

      <p className="result__meta">
        <RiskLabel risk={interaction.riskLevel} />
        <span>{formatDateTime(interaction.createdAt)}</span>
      </p>

      <p className="result__reason">{interaction.reason}</p>

      {!allowed && (
        <>
          <p className="result__reason">
            El contenido no se envió al generador de respuestas de la IA.
          </p>
          {detectedTypes.length > 0 && (
            <div className="section">
              <h3 className="section__title">Información detectada</h3>
              <div className="detected-types">
                {detectedTypes.map((type) => (
                  <span className="tag" key={type}>
                    {type}
                  </span>
                ))}
              </div>
              <div className="section">
                <h3 className="section__title">Hallazgos enmascarados</h3>
                <FindingsList findings={interaction.maskedFindings} />
              </div>
            </div>
          )}
        </>
      )}

      {allowed && !askedSomething && (
        <p className="result__reason">
          No escribiste una consulta, por lo que no se generó una respuesta. Añade una pregunta si
          quieres que el asistente trabaje con este documento.
        </p>
      )}

      {passedReviewButHasNoAnswer(interaction) && (
        <p className="notice notice--error" role="alert">
          El contenido superó la revisión, pero no fue posible generar la respuesta.
          {interaction.generationError ? ` ${interaction.generationError}` : ''}
        </p>
      )}

      {answer && (
        <div className="answer">
          <h3 className="section__title">Respuesta del asistente local</h3>
          <p className="answer__text">{answer.text}</p>
          <p className="answer__source">
            Generada por {answer.modelName} · {formatDateTime(answer.generatedAt)}
          </p>
        </div>
      )}

      <div className="form-actions">
        <button type="button" className="button button--primary" onClick={onNewQuery}>
          {allowed ? 'Realizar una nueva consulta' : 'Editar y volver a intentar'}
        </button>
        <Link to={`/historial/${interaction.id}`}>Ver el detalle en el historial</Link>
      </div>
    </section>
  )
}
