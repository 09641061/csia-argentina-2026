import { ArrowUp, FileJson2, Image, Paperclip, ShieldAlert, X } from 'lucide-react'
import { useMemo, useRef, useState, type ChangeEvent } from 'react'
import { Link } from 'react-router-dom'

import { SubmitSecureQuery } from '@/contexts/decision/application/submit-secure-query'
import type { SecureQueryOutcome } from '@/contexts/decision/domain/secure-interaction'
import { decisionLabel } from '@/contexts/decision/domain/secure-interaction'
import { HttpDecisionRepository } from '@/contexts/decision/infrastructure/http-decision-repository'
import { apiErrorMessage } from '@/shared/infrastructure/api/api-error'
import { ClaudeSpark } from '@/shared/interfaces/components/claude-brand'
import { ErrorNotice } from '@/shared/interfaces/components/error-notice'
import { FindingsList } from '@/shared/interfaces/components/findings-list'
import { RiskLabel } from '@/shared/interfaces/components/risk-label'
import { Alert, AlertDescription, AlertTitle } from '@/shared/interfaces/ui/alert'
import { Badge } from '@/shared/interfaces/ui/badge'
import { Button } from '@/shared/interfaces/ui/button'
import { Spinner } from '@/shared/interfaces/ui/spinner'
import { Textarea } from '@/shared/interfaces/ui/textarea'

export function SecureQueryPage() {
  const repository = useMemo(() => new HttpDecisionRepository(), [])
  const useCase = useRef(new SubmitSecureQuery(repository))
  const fileInput = useRef<HTMLInputElement>(null)
  const [prompt, setPrompt] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<SecureQueryOutcome | null>(null)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async () => {
    setIsSending(true); setError(null); setResult(null)
    try { setResult(await useCase.current.execute({ prompt, file })) }
    catch (caught) { setError(apiErrorMessage(caught)) }
    finally { setIsSending(false) }
  }

  const chooseFile = (event: ChangeEvent<HTMLInputElement>) => setFile(event.target.files?.[0] ?? null)
  const reset = () => { setPrompt(''); setFile(null); setResult(null); setError(null); if (fileInput.current) fileInput.current.value = '' }

  return (
    <div className="min-h-full bg-[#1b1b1a] px-4 pb-16 pt-24 text-[#f3f1ea] sm:px-8">
      <section className="mx-auto w-full max-w-[840px]">
        <header className="mb-8 text-center"><div className="mb-4 flex items-center justify-center gap-3"><ClaudeSpark className="size-9" /><h1 className="font-serif text-3xl sm:text-4xl">Consulta segura</h1></div><p className="mx-auto max-w-2xl text-sm leading-6 text-[#96958d]">Analiza mensajes y archivos antes de pedir una respuesta al modelo. El contenido bloqueado nunca llega al generador.</p></header>
        <div className="overflow-hidden rounded-[24px] border border-white/[0.05] bg-[#363633] shadow-[0_18px_55px_rgba(0,0,0,.25)]">
          <Textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={4} maxLength={8_000} disabled={isSending} placeholder="Escribe una consulta o adjunta un documento para revisarlo…" className="min-h-[112px] resize-none border-0 bg-transparent px-6 pb-2 pt-5 text-[16px] leading-7 shadow-none placeholder:text-[#aaa89f] focus-visible:ring-0" />
          {file && <div className="mx-4 mb-3 flex max-w-sm items-center gap-3 rounded-xl bg-black/20 px-3 py-2.5"><span className="grid size-9 place-items-center rounded-lg bg-white/[0.06]">{file.type.startsWith('image/') ? <Image className="size-[18px]" /> : <FileJson2 className="size-[18px]" />}</span><span className="min-w-0 flex-1"><span className="block truncate text-sm">{file.name}</span><span className="text-xs text-[#96958d]">{(file.size / 1024).toLocaleString('es', { maximumFractionDigits: 0 })} KB</span></span><Button type="button" variant="ghost" size="icon-sm" onClick={() => setFile(null)} aria-label="Quitar archivo"><X /></Button></div>}
          <div className="flex items-center gap-3 px-4 pb-3"><input ref={fileInput} id="secure-file" type="file" accept="application/json,image/png,image/jpeg" className="sr-only" onChange={chooseFile} /><Button asChild variant="ghost" size="icon" className="rounded-full border border-white/15"><label htmlFor="secure-file" title="Adjuntar JSON, PNG o JPEG"><Paperclip /><span className="sr-only">Adjuntar archivo</span></label></Button><span className="text-xs text-[#96958d]">Revisión y decisión local</span><Button type="button" size="icon" className="ml-auto rounded-full bg-[#eceae3] text-[#222220] hover:bg-white" disabled={isSending || (!prompt.trim() && !file)} onClick={submit} aria-label="Enviar consulta segura">{isSending ? <Spinner /> : <ArrowUp />}</Button></div>
        </div>
        <p className="mt-3 text-center text-[11px] text-[#77766f]">JSON, PNG o JPEG · máximo 10 MB · hasta 8.000 caracteres</p>
        {error && <div className="mt-5"><ErrorNotice message={error} onRetry={submit} /></div>}
        {result && <div className="mt-7"><QueryResult result={result} onReset={reset} /></div>}
      </section>
    </div>
  )
}

function QueryResult({ result, onReset }: { readonly result: SecureQueryOutcome; readonly onReset: () => void }) {
  const { interaction, answer } = result
  const allowed = interaction.decision === 'allowed'
  return <article className="claude-panel overflow-hidden"><header className="flex flex-wrap items-start justify-between gap-4 border-b border-white/[0.07] p-5 sm:p-6"><div><div className="flex items-center gap-2"><Badge className={allowed ? 'bg-[#2d3931] text-[#aed2b6]' : 'bg-[#3b2925] text-[#eda08b]'}>{decisionLabel(interaction.decision)}</Badge><RiskLabel risk={interaction.riskLevel} /></div><h2 className="mt-4 text-lg font-medium">{interaction.contentReference}</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-[#aaa89f]">{interaction.reason}</p></div></header><div className="space-y-6 p-5 sm:p-6">{!allowed && <Alert className="border-[#74433a]/60 bg-[#352522] text-[#f5c1b4]"><ShieldAlert /><AlertTitle>Generación detenida</AlertTitle><AlertDescription>El contenido no se envió al modelo de respuestas.</AlertDescription></Alert>}{interaction.maskedFindings.length > 0 && <section><h3 className="mb-3 text-sm font-medium">Evidencia enmascarada</h3><FindingsList findings={interaction.maskedFindings} /></section>}{answer && <section className="rounded-2xl bg-[#1d1d1c] p-5"><h3 className="flex items-center gap-2 text-sm text-[#c9c7bf]"><ClaudeSpark className="size-5" /> Respuesta local</h3><p className="mt-4 whitespace-pre-wrap text-[15px] leading-7">{answer.text}</p><p className="mt-5 text-xs text-[#77766f]">Modelo {answer.modelName}</p></section>}<div className="flex flex-wrap gap-3"><Button type="button" variant="outline" onClick={onReset}>Nueva consulta segura</Button><Button asChild variant="ghost"><Link to={`/auditoria/${interaction.id}`}>Ver registro de auditoría</Link></Button></div></div></article>
}

