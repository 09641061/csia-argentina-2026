import { useEffect, useState, type ReactNode } from 'react'
import {
  Activity, ArrowRight, CheckCircle2, Clipboard, Clock3, FileCheck2,
  FlaskConical, Play, Radar, Save, ShieldAlert, ShieldCheck, Siren, UserRound, XCircle,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { request } from '@/shared/api/http-client'
import { formatDateTime } from '@/shared/lib/format'

type Incident = { id:number; code:string; title:string; severity:string; status:string; actor:string; summary:string; rule_id:string; event_count:number; assignee:string|null; response_action:string|null; created_at:string }
type Overview = { total:number; event_count:number; open_incidents:number; critical_incidents:number; contained_incidents:number; pending_approvals:number; top_rules:Record<string,number>; incidents:Incident[] }
type Approval = { id:number; interaction_id:number; requester:string; status:string; reason:string; reviewer:string|null; comment?:string|null; created_at:string }
type Policy = { id:number; name:string; mode:'strict'|'corporate'|'custom'; version:number; rules:Record<string,unknown> }
type Scenario = { id:string; name:string; risk:string; sample:string }

const tone: Record<string, string> = {
  critical: 'border-red-500/30 bg-red-500/10 text-red-400', high: 'border-orange-500/30 bg-orange-500/10 text-orange-400',
  medium: 'border-amber-500/30 bg-amber-500/10 text-amber-300', low: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400',
  open: 'border-red-500/30 bg-red-500/10 text-red-400', investigating: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
  contained: 'border-blue-500/30 bg-blue-500/10 text-blue-400', closed: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400',
  pending: 'border-amber-500/30 bg-amber-500/10 text-amber-300', approved: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400', rejected: 'border-red-500/30 bg-red-500/10 text-red-400',
}

function StatusBadge({ value }: { value:string }) {
  return <Badge variant="outline" className={tone[value] ?? ''}>{value.replace('_', ' ')}</Badge>
}

function PageHeading({ eyebrow, title, description, action }: {eyebrow:string; title:string; description:string; action?:ReactNode}) {
  return <header className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-primary">{eyebrow}</p><h1 className="page-heading">{title}</h1><p className="page-description">{description}</p></div>{action}</header>
}

function Metric({ label, value, Icon, alert = false }: {label:string; value:number|string; Icon:LucideIcon; alert?:boolean}) {
  return <Card className="flex items-center gap-4 p-5 shadow-none"><span className={`grid size-11 place-items-center rounded-xl ${alert ? 'bg-red-500/10 text-red-400' : 'bg-primary/10 text-primary'}`}><Icon className="size-5" /></span><span><small className="block text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</small><strong className="text-2xl tabular-nums">{value}</strong></span></Card>
}

export function SecurityCenterPage() {
  const [data, setData] = useState<Overview | null>(null)
  const [selected, setSelected] = useState<Incident | null>(null)
  const load = () => request<Overview>('/api/v1/platform/overview').then(value => { setData(value); setSelected(current => current ?? value.incidents[0] ?? null) })
  useEffect(() => { void load() }, [])
  const update = async (status:'investigating'|'contained'|'closed') => {
    if (!selected) return
    const next = await request<Incident>(`/api/v1/platform/incidents/${selected.id}`, {method:'PUT', body:{status, assignee:'Analista SOC', response_action: status === 'contained' ? 'Sesión restringida y evidencia preservada.' : 'Caso revisado por el equipo SOC.'}})
    setSelected(next); await load()
  }
  return <>
    <PageHeading eyebrow="SOC workspace" title="Centro de seguridad" description="Detectá, correlacioná e investigá actividad de riesgo desde una única consola." action={<div className="flex items-center gap-2 rounded-xl border bg-card px-4 py-3 text-xs"><span className="size-2 rounded-full bg-emerald-400 shadow-[0_0_10px_currentColor]" /> Correlación activa</div>} />
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <Metric label="Eventos normalizados" value={data?.event_count ?? '—'} Icon={Activity} />
      <Metric label="Incidentes abiertos" value={data?.open_incidents ?? '—'} Icon={Siren} />
      <Metric label="Críticos" value={data?.critical_incidents ?? '—'} Icon={ShieldAlert} alert />
      <Metric label="Contenidos" value={data?.contained_incidents ?? '—'} Icon={ShieldCheck} />
    </div>
    <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(20rem,.75fr)]">
      <Card className="overflow-hidden py-0 shadow-none"><div className="flex items-center justify-between border-b px-5 py-4"><div><h2 className="text-sm font-semibold">Cola de incidentes</h2><p className="text-xs text-muted-foreground">Eventos relacionados por usuario, regla y ventana temporal</p></div><Badge variant="outline">{data?.incidents.length ?? 0} casos</Badge></div>
        <div>{data?.incidents.length ? data.incidents.map(item => <button type="button" onClick={() => setSelected(item)} className={`grid w-full grid-cols-[auto_1fr_auto] items-center gap-3 border-b px-5 py-4 text-left transition-colors last:border-0 hover:bg-muted/40 ${selected?.id === item.id ? 'bg-primary/5' : ''}`} key={item.id}><span className={`size-2 rounded-full ${item.severity === 'critical' ? 'bg-red-400' : item.severity === 'high' ? 'bg-orange-400' : 'bg-amber-300'}`} /><span className="min-w-0"><span className="flex flex-wrap items-center gap-2"><strong className="text-sm">{item.title}</strong><code className="text-[10px] text-muted-foreground">{item.code}</code></span><small className="mt-1 block text-xs text-muted-foreground">{item.event_count} eventos · {item.actor} · regla {item.rule_id}</small></span><StatusBadge value={item.status} /></button>) : <p className="p-8 text-center text-sm text-muted-foreground">No hay incidentes activos. Ejecutá un escenario desde Laboratorio para probar la correlación.</p>}</div>
      </Card>
      <Card className="p-6 shadow-none">{selected ? <div className="space-y-5"><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-medium text-muted-foreground">{selected.code}</p><h2 className="mt-1 text-lg font-semibold">{selected.title}</h2></div><StatusBadge value={selected.severity} /></div><p className="text-sm leading-6 text-muted-foreground">{selected.summary}</p><dl className="grid grid-cols-2 gap-4 rounded-xl border bg-background/30 p-4"><SocDetail label="Actor" value={selected.actor} /><SocDetail label="Regla" value={selected.rule_id} /><SocDetail label="Eventos" value={String(selected.event_count)} /><SocDetail label="Analista" value={selected.assignee ?? 'Sin asignar'} /></dl>{selected.response_action && <div className="rounded-xl border border-primary/20 bg-primary/5 p-4"><p className="text-xs font-semibold text-primary">Respuesta aplicada</p><p className="mt-1 text-xs text-muted-foreground">{selected.response_action}</p></div>}<div className="flex flex-wrap gap-2">{selected.status === 'open' && <Button onClick={() => void update('investigating')}><UserRound /> Investigar</Button>}{selected.status !== 'contained' && selected.status !== 'closed' && <Button variant="outline" onClick={() => void update('contained')}><ShieldCheck /> Contener</Button>}{selected.status !== 'closed' && <Button variant="ghost" onClick={() => void update('closed')}>Cerrar caso</Button>}</div></div> : <div className="grid min-h-72 place-items-center text-center"><div><Radar className="mx-auto size-8 text-muted-foreground" /><p className="mt-3 text-sm text-muted-foreground">Seleccioná un incidente para investigar.</p></div></div>}</Card>
    </div>
    <Card className="mt-4 p-5 shadow-none"><h2 className="mb-4 text-sm font-semibold">Reglas más activadas</h2><div className="grid gap-3 sm:grid-cols-3">{Object.entries(data?.top_rules ?? {}).map(([rule,count]) => <div className="flex items-center justify-between rounded-lg border bg-background/30 p-3" key={rule}><code className="text-xs text-primary">{rule}</code><strong className="text-sm">{count}</strong></div>)}</div></Card>
  </>
}

function SocDetail({label,value}:{label:string;value:string}) { return <div><dt className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</dt><dd className="mt-1 text-xs font-semibold">{value}</dd></div> }

export function ApprovalsPage() {
  const [items, setItems] = useState<Approval[]>([])
  const [tab, setTab] = useState<'pending'|'resolved'>('pending')
  const load = () => request<Approval[]>('/api/v1/platform/approvals').then(setItems)
  useEffect(() => { void load() }, [])
  const visible = items.filter(item => tab === 'pending' ? item.status === 'pending' : item.status !== 'pending')
  const resolve = async (id:number, action:'approved'|'rejected') => { await request(`/api/v1/platform/approvals/${id}/resolve`, {method:'POST', body:{action, comment: action === 'approved' ? 'Versión segura autorizada.' : 'Operación rechazada por el SOC.'}}); await load() }
  return <><PageHeading eyebrow="Investigation queue" title="Aprobaciones" description="Revisá excepciones, preservá evidencia y registrá cada decisión humana." />
    <div className="mb-4 flex gap-1 rounded-lg border bg-card p-1 sm:w-fit"><Button variant={tab==='pending'?'secondary':'ghost'} onClick={() => setTab('pending')}><Clock3 /> Pendientes <Badge variant="outline">{items.filter(i=>i.status==='pending').length}</Badge></Button><Button variant={tab==='resolved'?'secondary':'ghost'} onClick={() => setTab('resolved')}><CheckCircle2 /> Resueltos</Button></div>
    <Card className="overflow-hidden py-0 shadow-none">{visible.length ? visible.map(item => <article className="flex flex-col justify-between gap-4 border-b p-5 last:border-0 sm:flex-row sm:items-center" key={item.id}><div className="min-w-0"><div className="flex items-center gap-2"><StatusBadge value={item.status} /><code className="text-[10px] text-muted-foreground">REV-{String(item.id).padStart(4,'0')}</code></div><h3 className="mt-3 text-sm font-semibold">Interacción #{item.interaction_id}</h3><p className="mt-1 text-sm text-muted-foreground">{item.reason}</p><small className="mt-2 block text-xs text-muted-foreground">Solicitado por {item.requester} · {formatDateTime(item.created_at)}</small>{item.comment && <p className="mt-2 text-xs text-primary">{item.comment}</p>}</div>{item.status === 'pending' && <div className="flex shrink-0 gap-2"><Button variant="outline" onClick={() => void resolve(item.id,'rejected')}><XCircle /> Rechazar</Button><Button onClick={() => void resolve(item.id,'approved')}><FileCheck2 /> Aprobar versión segura</Button></div>}</article>) : <div className="grid min-h-64 place-items-center text-center"><div><CheckCircle2 className="mx-auto size-8 text-emerald-400"/><p className="mt-3 text-sm text-muted-foreground">No hay elementos en esta cola.</p></div></div>}</Card></>
}

export function PoliciesPage() {
  const [policy, setPolicy] = useState<Policy | null>(null); const [saved,setSaved] = useState(false)
  useEffect(() => { void request<Policy>('/api/v1/platform/policies/current').then(setPolicy) }, [])
  const save = async () => { if (!policy) return; const next = await request<Policy>('/api/v1/platform/policies/current',{method:'PUT',body:{name:policy.name,mode:policy.mode,rules:policy.rules}}); setPolicy(next); setSaved(true) }
  const correlations = [{rule:'CORR-001',title:'Intentos reiterados',when:'3 bloqueos del mismo actor en 10 minutos',then:'Incidente alto'}, {rule:'CORR-002',title:'Exfiltración probable',when:'Credencial + intento de evasión',then:'Incidente crítico'}, {rule:'CORR-003',title:'Abuso de instrucciones',when:'Prompt injection + acceso sensible',then:'Contención automática'}]
  return <><PageHeading eyebrow="Detection engineering" title="Políticas" description="Definí cómo proteger cada dato y cuándo varios eventos se convierten en un incidente." action={policy && <Badge variant="outline">Política v{policy.version}</Badge>} />
    <div className="grid gap-4 xl:grid-cols-[.8fr_1.2fr]"><Card className="p-5 shadow-none"><h2 className="mb-4 text-sm font-semibold">Postura de protección</h2><div className="grid gap-2">{(['strict','corporate','custom'] as const).map(mode => <button className={`flex gap-3 rounded-xl border p-4 text-left transition-colors ${policy?.mode===mode?'border-primary bg-primary/5':'hover:bg-muted/40'}`} key={mode} onClick={() => policy && setPolicy({...policy,mode})}><ShieldCheck className="size-5 text-primary"/><span><strong className="block text-sm">{mode==='strict'?'Estricto':mode==='corporate'?'Corporativo':'Personalizado'}</strong><small className="text-xs text-muted-foreground">{mode==='strict'?'Bloqueo preventivo para cualquier hallazgo':mode==='corporate'?'Protección y continuidad operativa':'Reglas adaptadas al entorno'}</small></span></button>)}</div><h2 className="mb-3 mt-6 text-sm font-semibold">Acciones por categoría</h2>{Object.entries(policy?.rules ?? {}).map(([key,value]) => <div className="flex justify-between border-t py-3 text-xs" key={key}><span className="capitalize text-muted-foreground">{key.replace('_',' ')}</span><Badge variant="outline">{String(value)}</Badge></div>)}<Button className="mt-4" onClick={() => void save()}><Save /> Publicar política</Button>{saved && <span className="ml-3 text-xs text-emerald-400">Versión publicada</span>}</Card>
      <Card className="p-5 shadow-none"><div className="mb-4 flex items-center justify-between"><div><h2 className="text-sm font-semibold">Reglas de correlación</h2><p className="mt-1 text-xs text-muted-foreground">Agrupan señales aisladas para detectar una amenaza completa.</p></div><Badge className="bg-emerald-500/10 text-emerald-400">3 activas</Badge></div><div className="space-y-3">{correlations.map(item => <article className="rounded-xl border bg-background/30 p-4" key={item.rule}><div className="flex items-start justify-between"><div><code className="text-[10px] text-primary">{item.rule}</code><h3 className="mt-1 text-sm font-semibold">{item.title}</h3></div><span className="size-2 rounded-full bg-emerald-400" /></div><div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto_1fr]"><div className="rounded-lg bg-muted/40 p-3"><small className="text-[10px] uppercase text-muted-foreground">Cuando</small><p className="mt-1 text-xs">{item.when}</p></div><ArrowRight className="m-auto size-4 text-muted-foreground"/><div className="rounded-lg bg-primary/5 p-3"><small className="text-[10px] uppercase text-primary">Entonces</small><p className="mt-1 text-xs">{item.then}</p></div></div></article>)}</div></Card></div></>
}

export function SecurityLabPage() {
  const [items,setItems] = useState<Scenario[]>([]); const [running,setRunning] = useState(''); const [result,setResult] = useState<Incident|null>(null); const [copied,setCopied] = useState('')
  useEffect(() => { void request<Scenario[]>('/api/v1/platform/lab/scenarios').then(setItems) }, [])
  const run = async (item:Scenario) => { setRunning(item.id); setResult(null); try { setResult(await request<Incident>(`/api/v1/platform/lab/scenarios/${item.id}/run`,{method:'POST'})) } finally { setRunning('') } }
  const copy = async (item:Scenario) => { await navigator.clipboard.writeText(item.sample); setCopied(item.id) }
  return <><PageHeading eyebrow="SOC simulation" title="Laboratorio" description="Ejecutá cadenas de ataque seguras y comprobá cómo Sentinel detecta, correlaciona y contiene." />
    {result && <Card className="mb-5 border-primary/30 bg-primary/5 p-5 shadow-none"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center"><div className="flex items-start gap-3"><span className="grid size-10 place-items-center rounded-xl bg-emerald-500/10 text-emerald-400"><CheckCircle2 className="size-5"/></span><div><p className="text-xs font-semibold text-primary">Simulación completada · {result.code}</p><h2 className="mt-1 font-semibold">{result.title}</h2><p className="mt-1 text-xs text-muted-foreground">{result.event_count} eventos correlacionados · {result.response_action}</p></div></div><Button asChild variant="outline"><a href="/seguridad">Ver en Seguridad <ArrowRight /></a></Button></div></Card>}
    <div className="grid gap-4 lg:grid-cols-2">{items.map(item => <Card className="p-5 shadow-none" key={item.id}><div className="flex justify-between"><span className="grid size-10 place-items-center rounded-xl bg-primary/10 text-primary"><FlaskConical className="size-5"/></span><StatusBadge value={item.risk} /></div><h2 className="mt-4 font-semibold">{item.name}</h2><code className="mt-3 block min-h-16 rounded-lg bg-muted/40 p-3 text-xs leading-5 text-muted-foreground whitespace-normal">{item.sample}</code><div className="mt-4 flex gap-2"><Button onClick={() => void run(item)} disabled={Boolean(running)}><Play />{running===item.id?'Correlacionando…':'Ejecutar simulación'}</Button><Button variant="outline" onClick={() => void copy(item)}><Clipboard />{copied===item.id?'Copiado':'Copiar muestra'}</Button></div></Card>)}</div></>
}
