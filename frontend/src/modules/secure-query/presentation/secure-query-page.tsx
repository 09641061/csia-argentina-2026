import { useMemo } from 'react'
import { Activity, Braces, CheckCircle2, Cpu, Database, Eye, LockKeyhole, ScanSearch, ShieldCheck } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { HttpSecureQueryRepository } from '@/modules/secure-query/infrastructure/http-secure-query-repository'
import { ErrorNotice } from '@/shared/ui/error-notice'
import { LoadingStatus } from '@/shared/ui/loading-status'
import { SecureQueryForm } from './secure-query-form'
import { SecureQueryResult } from './secure-query-result'
import { useSecureQuery } from './use-secure-query'

const ENVIRONMENT = [[Cpu, 'Motor activo', 'Versión 2.1'], [Eye, 'Escaneo visual', 'Habilitado'], [Database, 'Registro local', 'Conectado']] as const
const CONTROLS = [[ScanSearch, 'Inspección', 'Busca datos sensibles'], [Braces, 'Política', 'Evalúa el nivel de riesgo'], [ShieldCheck, 'Respuesta', 'Registra una salida segura']] as const

export function SecureQueryPage() {
  const repository = useMemo(() => new HttpSecureQueryRepository(), [])
  const { state, setPrompt, setDocument, submit, reset } = useSecureQuery(repository)
  const isBusy = state.phase === 'analyzing' || state.phase === 'generating'

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div><p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-primary">Nueva revisión · Canal 001</p><h1 className="page-heading">Consultar</h1><p className="page-description">Prepará y revisá contenido dentro de un entorno protegido.</p></div>
        <div className="flex items-center gap-3 rounded-xl border bg-card px-4 py-3"><span className="grid size-9 place-items-center rounded-lg bg-emerald-500/10 text-emerald-400"><CheckCircle2 className="size-4" /></span><span><strong className="block text-sm">Sistemas listos</strong><small className="text-xs text-muted-foreground">Monitoreo en tiempo real</small></span></div>
      </header>

      <section className="grid grid-cols-2 gap-px overflow-hidden rounded-xl border bg-border sm:grid-cols-4" aria-label="Estado del entorno">
        {ENVIRONMENT.map(([Icon, label, value]) => <div className="flex items-center gap-3 bg-card p-4" key={label}><Icon className="size-4 text-primary" /><span><small className="block text-[10px] uppercase tracking-wider text-muted-foreground">{label}</small><strong className="text-sm">{value}</strong></span></div>)}
        <div className="flex items-center gap-3 bg-card p-4"><Activity className="size-4 text-emerald-400" /><span><small className="block text-[10px] uppercase tracking-wider text-muted-foreground">Postura</small><strong className="text-sm text-emerald-400">Óptima</strong></span></div>
      </section>

      <div className="grid items-stretch gap-4 lg:grid-cols-[minmax(0,1fr)_19rem]">
        <Card className="overflow-hidden border-border/80 bg-card py-0 shadow-none">
          <div className="flex items-center justify-between border-b px-5 py-3"><div className="flex items-center gap-2"><span className="flex gap-1"><i className="size-1.5 rounded-full bg-red-400"/><i className="size-1.5 rounded-full bg-amber-400"/><i className="size-1.5 rounded-full bg-emerald-400"/></span><code className="text-[11px] text-muted-foreground">secure-input.channel</code></div><Badge variant="outline" className="gap-1.5"><LockKeyhole className="size-3" /> Sesión privada</Badge></div>
          <SecureQueryForm draft={state.draft} isBusy={isBusy} onPromptChange={setPrompt} onDocumentChange={setDocument} onSubmit={submit} />
        </Card>

        <Card className="relative overflow-hidden border-border/80 bg-card p-6 shadow-none">
          <div className="absolute -right-20 -top-20 size-56 rounded-full bg-primary/8 blur-3xl" />
          <div className="relative flex items-start justify-between"><div><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-primary">Monitor en vivo</p><h2 className="mt-1 text-xl font-semibold">Perímetro Sentinel</h2></div><Badge className="bg-emerald-500/10 text-emerald-400">Activo</Badge></div>
          <div className="relative my-7 grid place-items-center"><div className="grid size-32 place-items-center rounded-full border border-primary/20"><div className="grid size-20 place-items-center rounded-full border border-primary/30"><span className="grid size-11 place-items-center rounded-full bg-primary text-primary-foreground"><ShieldCheck className="size-5" /></span></div></div><span className="absolute right-[28%] top-[18%] size-2 rounded-full bg-emerald-400 shadow-[0_0_12px_currentColor]" /><span className="absolute bottom-[18%] left-[28%] size-2 rounded-full bg-amber-300 shadow-[0_0_12px_currentColor]" /></div>
          <p className="text-center text-xs leading-5 text-muted-foreground">Cada consulta atraviesa tres controles antes de procesarse.</p>
          <ol className="mt-6 space-y-2">{CONTROLS.map(([Icon, title, copy], index) => <li className="flex items-center gap-3 rounded-lg border bg-background/30 p-3" key={title}><span className="grid size-8 place-items-center rounded-md bg-primary/10 text-primary"><Icon className="size-4" /></span><div className="min-w-0 flex-1"><strong className="block text-xs">{title}</strong><small className="text-[11px] text-muted-foreground">{copy}</small></div><span className="text-[10px] tabular-nums text-muted-foreground">0{index + 1}</span></li>)}</ol>
        </Card>
      </div>

      {state.phase === 'analyzing' && <LoadingStatus message="Analizando el contenido…" />}
      {state.phase === 'generating' && <LoadingStatus message="Contenido permitido. Generando la respuesta…" />}
      {state.phase === 'error' && state.errorMessage && <ErrorNotice message={state.errorMessage} onRetry={submit} />}
      {state.phase === 'done' && state.interaction && <SecureQueryResult interaction={state.interaction} answer={state.answer} originalPrompt={state.draft.prompt} onNewQuery={reset} />}
    </div>
  )
}
