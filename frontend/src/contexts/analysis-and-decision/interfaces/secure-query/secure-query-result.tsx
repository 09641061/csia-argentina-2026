import { ArrowRight, CheckCircle2, RotateCcw, ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'

import { includesPrompt } from '@/contexts/analysis-and-decision/domain/analysis/content-type'
import { decisionLabel } from '@/contexts/analysis-and-decision/domain/analysis/decision'
import { detectedInformationTypes } from '@/contexts/analysis-and-decision/domain/analysis/finding'
import type { AssistantResponse } from '@/contexts/analysis-and-decision/domain/secure-query/assistant-response'
import {
  passedReviewButHasNoAnswer,
  wasAllowed,
  type SecureInteraction,
} from '@/contexts/analysis-and-decision/domain/secure-query/secure-interaction'
import { formatDateTime } from '@/shared/lib/format'
import { ClaudeSpark } from '@/shared/interfaces/components/claude-brand'
import { FindingsList } from '@/shared/interfaces/components/findings-list'
import { RiskLabel } from '@/shared/interfaces/components/risk-label'
import { Alert, AlertDescription, AlertTitle } from '@/shared/interfaces/ui/alert'
import { Badge } from '@/shared/interfaces/ui/badge'
import { Button } from '@/shared/interfaces/ui/button'
import { Separator } from '@/shared/interfaces/ui/separator'

interface SecureQueryResultProps {
  readonly interaction: SecureInteraction
  readonly answer: AssistantResponse | null
  readonly onNewQuery: () => void
}

export function SecureQueryResult({ interaction, answer, onNewQuery }: SecureQueryResultProps) {
  const allowed = wasAllowed(interaction)
  const askedSomething = includesPrompt(interaction.contentType)
  const detectedTypes = detectedInformationTypes(interaction.maskedFindings)
  const title =
    allowed && !askedSomething ? 'Documento permitido' : decisionLabel(interaction.decision)

  return (
    <article
      className="overflow-hidden rounded-[22px] border border-white/[0.08] bg-[#242422] shadow-[0_20px_70px_rgba(0,0,0,0.22)]"
      aria-live="polite"
      data-testid="secure-query-result"
    >
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-white/[0.07] px-5 py-5 sm:px-6">
        <div className="flex items-start gap-3.5">
          <span
            className={`grid size-10 shrink-0 place-items-center rounded-xl ${
              allowed ? 'bg-[#29352e] text-[#a7cfb0]' : 'bg-[#3c2925] text-[#ef9d87]'
            } [&_svg]:size-5`}
          >
            {allowed ? <CheckCircle2 aria-hidden="true" /> : <ShieldAlert aria-hidden="true" />}
          </span>
          <div>
            <h2 className="text-base font-medium text-[#f4f2eb]">{title}</h2>
            <p className="mt-1 max-w-xl text-sm leading-6 text-[#aaa89f]">{interaction.reason}</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <RiskLabel risk={interaction.riskLevel} />
          <Badge variant="outline" className="border-white/10 bg-transparent text-[#aaa89f]">
            {formatDateTime(interaction.createdAt)}
          </Badge>
        </div>
      </header>

      <div className="flex flex-col gap-6 px-5 py-6 sm:px-6">
        {!allowed && (
          <>
            <Alert className="border-[#74433a]/60 bg-[#352522] text-[#f5c1b4]">
              <ShieldAlert aria-hidden="true" />
              <AlertTitle>Generación detenida</AlertTitle>
              <AlertDescription>
                El contenido no se envió al generador de respuestas de la IA.
              </AlertDescription>
            </Alert>
            {detectedTypes.length > 0 && (
              <section className="flex flex-col gap-4">
                <div>
                  <h3 className="text-sm font-medium text-[#e7e5dd]">Información detectada</h3>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {detectedTypes.map((type) => (
                      <Badge
                        key={type}
                        variant="secondary"
                        className="bg-white/[0.07] text-[#cbc9c0]"
                      >
                        {type}
                      </Badge>
                    ))}
                  </div>
                </div>
                <FindingsList findings={interaction.maskedFindings} />
              </section>
            )}
          </>
        )}

        {allowed && !askedSomething && (
          <Alert className="border-white/[0.08] bg-white/[0.035] text-[#c9c7bf]">
            <AlertDescription>
              No escribiste una consulta, por lo que no se generó una respuesta. Añade una pregunta
              para trabajar con el documento.
            </AlertDescription>
          </Alert>
        )}

        {passedReviewButHasNoAnswer(interaction) && (
          <Alert className="border-[#74433a]/60 bg-[#352522] text-[#f5c1b4]" role="alert">
            <AlertDescription>
              El contenido superó la revisión, pero no fue posible generar la respuesta.
              {interaction.generationError ? ` ${interaction.generationError}` : ''}
            </AlertDescription>
          </Alert>
        )}

        {answer && (
          <section className="rounded-2xl bg-[#1d1d1c] px-5 py-5">
            <h3 className="flex items-center gap-2.5 text-sm font-medium text-[#d7d5cd]">
              <ClaudeSpark className="size-[18px]" /> Respuesta del asistente local
            </h3>
            <p className="mt-4 whitespace-pre-wrap text-[15px] leading-7 text-[#efede6]">
              {answer.text}
            </p>
            <Separator className="my-5 bg-white/[0.08]" />
            <p className="text-xs text-[#85847d]">
              Generada por {answer.modelName} · {formatDateTime(answer.generatedAt)}
            </p>
          </section>
        )}
      </div>

      <footer className="flex flex-wrap gap-3 border-t border-white/[0.07] px-5 py-4 sm:px-6">
        <Button
          type="button"
          variant="secondary"
          className="rounded-xl bg-[#eceae3] text-[#222220] hover:bg-white"
          onClick={onNewQuery}
        >
          <RotateCcw aria-hidden="true" />
          {allowed ? 'Realizar una nueva consulta' : 'Editar y volver a intentar'}
        </Button>
        <Button
          asChild
          variant="ghost"
          className="rounded-xl text-[#bbb9b0] hover:bg-white/[0.06] hover:text-white"
        >
          <Link to={`/historial/${interaction.id}`}>
            Ver detalle <ArrowRight data-icon="inline-end" aria-hidden="true" />
          </Link>
        </Button>
      </footer>
    </article>
  )
}
