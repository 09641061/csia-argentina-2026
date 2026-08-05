import { ArrowRight, Bot, CheckCircle2, Download, FileCheck2, GitBranch, ShieldAlert, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { includesPrompt } from '@/modules/analysis/domain/content-type'
import { decisionLabel } from '@/modules/analysis/domain/decision'
import { detectedInformationTypes } from '@/modules/analysis/domain/finding'
import type { AssistantResponse } from '@/modules/secure-query/domain/assistant-response'
import {
  passedReviewButHasNoAnswer,
  wasAllowed,
  type SecureInteraction,
} from '@/modules/secure-query/domain/secure-interaction'
import { formatDateTime } from '@/shared/lib/format'
import { FindingsList } from '@/shared/ui/findings-list'
import { RiskLabel } from '@/shared/ui/risk-label'
import { request } from '@/shared/api/http-client'
import { apiBaseUrl } from '@/shared/config/env'

interface SecureQueryResultProps {
  readonly interaction: SecureInteraction
  readonly answer: AssistantResponse | null
  readonly originalPrompt?: string
  readonly onNewQuery: () => void
}

export function SecureQueryResult({ interaction, answer, originalPrompt = '', onNewQuery }: SecureQueryResultProps) {
  const allowed = wasAllowed(interaction)
  const askedSomething = includesPrompt(interaction.contentType)
  const detectedTypes = detectedInformationTypes(interaction.maskedFindings)

  return (
    <Card aria-live="polite" data-testid="secure-query-result">
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <span className="grid size-10 place-items-center rounded-lg bg-muted [&_svg]:size-5">
              {allowed ? <CheckCircle2 aria-hidden="true" /> : <ShieldAlert aria-hidden="true" />}
            </span>
            <div>
              <CardTitle>
                {allowed && !askedSomething
                  ? 'Documento permitido'
                  : decisionLabel(interaction.decision)}
              </CardTitle>
              <p className="mt-1 text-sm text-muted-foreground">{interaction.reason}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <RiskLabel risk={interaction.riskLevel} />
            <Badge variant="outline">{formatDateTime(interaction.createdAt)}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        {!allowed && (
          <>
            <Alert variant="destructive">
              <ShieldAlert aria-hidden="true" />
              <AlertTitle>Generación detenida</AlertTitle>
              <AlertDescription>
                El contenido no se envió al generador de respuestas de la IA.
              </AlertDescription>
            </Alert>
            {detectedTypes.length > 0 && (
              <section className="flex flex-col gap-4">
                <div>
                  <h3 className="text-sm font-semibold">Información detectada</h3>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {detectedTypes.map((type) => (
                      <Badge key={type} variant="secondary">
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
          <Alert>
            <AlertDescription>
              No escribiste una consulta, por lo que no se generó una respuesta. Añade una pregunta
              para trabajar con el documento.
            </AlertDescription>
          </Alert>
        )}

        {passedReviewButHasNoAnswer(interaction) && (
          <Alert variant="destructive" role="alert">
            <AlertDescription>
              El contenido superó la revisión, pero no fue posible generar la respuesta.
              {interaction.generationError ? ` ${interaction.generationError}` : ''}
            </AlertDescription>
          </Alert>
        )}

        {answer && (
          <section className="border-l-2 border-foreground pl-4">
            <h3 className="flex items-center gap-2 text-sm font-medium [&_svg]:size-4">
              <Bot aria-hidden="true" /> Respuesta del asistente local
            </h3>
            <p className="mt-4 whitespace-pre-wrap text-[15px] leading-7">{answer.text}</p>
            <Separator className="my-4" />
            <p className="text-xs text-muted-foreground">
              Generada por {answer.modelName} · {formatDateTime(answer.generatedAt)}
            </p>
          </section>
        )}
        <SecurityActions interaction={interaction} originalPrompt={originalPrompt} />
      </CardContent>
      <CardFooter className="flex-wrap gap-3">
        <Button type="button" onClick={onNewQuery}>
          {allowed ? 'Realizar una nueva consulta' : 'Editar y volver a intentar'}
        </Button>
        <Button asChild variant="ghost">
          <Link to={`/historial/${interaction.id}`}>
            Ver detalle <ArrowRight data-icon="inline-end" aria-hidden="true" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  )
}

type Trace = { steps: Array<{stage:string; status:string; label:string}> }
type Sanitized = { safe_content:string; replacements:Array<{category:string;token:string}> }

function SecurityActions({ interaction, originalPrompt }: { interaction: SecureInteraction; originalPrompt:string }) {
  const [trace,setTrace] = useState<Trace | null>(null)
  const [sanitized,setSanitized] = useState<Sanitized | null>(null)
  const [approval,setApproval] = useState(false)
  useEffect(() => { void request<Trace>(`/api/v1/platform/interactions/${interaction.id}/trace`).then(setTrace).catch(() => undefined) }, [interaction.id])
  const sanitize = async () => setSanitized(await request<Sanitized>('/api/v1/platform/sanitize',{method:'POST',body:{content:originalPrompt,interaction_id:interaction.id}}))
  const approve = async () => { await request('/api/v1/platform/approvals',{method:'POST',body:{interaction_id:interaction.id}}); setApproval(true) }
  return <section className="mt-2 space-y-3">
    <div className="rounded-xl border p-4"><h3 className="mb-3 flex items-center gap-2 text-sm font-medium"><GitBranch className="size-4 text-primary" /> Trazabilidad de la decisión</h3><div className="space-y-2">{trace?.steps.map(step => <div className="grid grid-cols-[8px_90px_1fr] items-center gap-2 text-xs" key={step.stage}><span className={`size-2 rounded-full ${step.status==='blocked'||step.status==='failed'?'bg-destructive':'bg-emerald-500'}`} /><strong className="uppercase">{step.stage}</strong><span className="text-muted-foreground">{step.label}</span></div>)}</div></div>
    {!wasAllowed(interaction) && <div className="rounded-xl bg-muted p-4"><h3 className="mb-3 flex items-center gap-2 text-sm font-medium"><ShieldCheck className="size-4 text-primary" /> Próximos pasos seguros</h3><div className="flex flex-wrap gap-2">
      {originalPrompt.trim() && <Button variant="outline" onClick={() => void sanitize()}>Crear versión segura</Button>}
      <Button variant="outline" onClick={() => void approve()} disabled={approval}><FileCheck2 />{approval?'Aprobación solicitada':'Solicitar aprobación'}</Button>
      <Button asChild variant="outline"><a href={`${apiBaseUrl}/api/v1/platform/reports/${interaction.id}.pdf`}><Download /> Reporte PDF</a></Button>
    </div>{sanitized && <div className="mt-3"><span className="text-xs text-primary">Versión sanitizada · {sanitized.replacements.length} reemplazos</span><pre className="mt-2 whitespace-pre-wrap rounded-lg border bg-background p-3 text-xs">{sanitized.safe_content}</pre></div>}</div>}
    {wasAllowed(interaction) && <Button asChild variant="link" className="px-0"><a href={`${apiBaseUrl}/api/v1/platform/reports/${interaction.id}.pdf`}><Download /> Descargar reporte de auditoría</a></Button>}
  </section>
}
