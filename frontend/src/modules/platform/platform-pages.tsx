import { useEffect, useState } from 'react'
import { AlertTriangle, BarChart3, CheckCircle2, Clipboard, FileCheck2, FlaskConical, Save, ShieldCheck } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { request } from '@/shared/api/http-client'

type Overview = { total: number; blocked: number; allowed: number; pending_approvals: number; risks: Record<string, number>; categories: Record<string, number>; recent: Array<{id:number; reference:string; decision:string; risk:string|null; created_at:string}> }
type Approval = { id:number; interaction_id:number; requester:string; status:string; reason:string; reviewer:string|null; created_at:string }
type Policy = { id:number; name:string; mode:'strict'|'corporate'|'custom'; version:number; rules:Record<string,unknown> }
type Scenario = { id:string; name:string; risk:string; sample:string }

function PageHeading({ eyebrow, title, description }: {eyebrow:string; title:string; description:string}) {
  return <header className="workspace-heading"><div><p className="workspace-heading__eyebrow">{eyebrow}</p><h1 className="page-title">{title}</h1><p className="page-lead">{description}</p></div></header>
}

export function SecurityCenterPage() {
  const [data, setData] = useState<Overview | null>(null)
  const metrics: Array<[string, number | string, LucideIcon]> = [['Interacciones', data?.total ?? '—', BarChart3], ['Permitidas', data?.allowed ?? '—', CheckCircle2], ['Bloqueadas', data?.blocked ?? '—', AlertTriangle], ['Pendientes', data?.pending_approvals ?? '—', FileCheck2]]
  useEffect(() => { void request<Overview>('/api/v1/platform/overview').then(setData) }, [])
  return <><PageHeading eyebrow="Control room" title="Centro de seguridad" description="Visibilidad ejecutiva sobre el uso seguro de IA." />
    <div className="metric-grid">
      {metrics.map(([label,value,Icon]) => <Card className="metric-card" key={label}><Icon /><small>{label}</small><strong>{String(value)}</strong></Card>)}
    </div>
    <div className="platform-grid"><Card className="platform-card"><h2>Actividad reciente</h2>{data?.recent.length ? <div className="event-list">{data.recent.map(item => <div key={item.id}><span className={`event-dot event-dot--${item.decision}`} /><div><strong>{item.reference}</strong><small>Riesgo {item.risk ?? 'N/D'}</small></div><b>{item.decision}</b></div>)}</div> : <p className="platform-muted">Todavía no hay actividad registrada.</p>}</Card>
      <Card className="platform-card"><h2>Información detectada</h2><div className="category-bars">{Object.entries(data?.categories ?? {}).map(([name,value]) => <div key={name}><span>{name}</span><i><b style={{width:`${Math.min(100,value*18)}%`}} /></i><strong>{value}</strong></div>)}</div></Card></div></>
}

export function ApprovalsPage() {
  const [items, setItems] = useState<Approval[]>([])
  const load = () => request<Approval[]>('/api/v1/platform/approvals').then(setItems)
  useEffect(() => { void load() }, [])
  const resolve = async (id:number, action:'approved'|'rejected') => { await request(`/api/v1/platform/approvals/${id}/resolve`, {method:'POST', body:{action}}); await load() }
  return <><PageHeading eyebrow="Human in the loop" title="Aprobaciones" description="Decisiones sensibles que requieren una segunda mirada." /><Card className="platform-card"><div className="approval-list">{items.length ? items.map(item => <article key={item.id}><div><span className={`approval-status approval-status--${item.status}`}>{item.status}</span><h3>Interacción #{item.interaction_id}</h3><p>{item.reason}</p><small>Solicitado por {item.requester}</small></div>{item.status === 'pending' && <div><Button variant="outline" onClick={() => void resolve(item.id,'rejected')}>Rechazar</Button><Button onClick={() => void resolve(item.id,'approved')}>Aprobar</Button></div>}</article>) : <p className="platform-muted">No hay solicitudes pendientes.</p>}</div></Card></>
}

export function PoliciesPage() {
  const [policy, setPolicy] = useState<Policy | null>(null); const [saved,setSaved] = useState(false)
  useEffect(() => { void request<Policy>('/api/v1/platform/policies/current').then(setPolicy) }, [])
  const save = async () => { if (!policy) return; const next = await request<Policy>('/api/v1/platform/policies/current',{method:'PUT',body:{name:policy.name,mode:policy.mode,rules:policy.rules}}); setPolicy(next); setSaved(true) }
  return <><PageHeading eyebrow="Policy engine" title="Políticas" description="Definí cómo debe reaccionar Sentinel ante cada clase de riesgo." /><div className="policy-layout"><Card className="platform-card policy-modes">{(['strict','corporate','custom'] as const).map(mode => <button className={policy?.mode===mode?'active':''} key={mode} onClick={() => policy && setPolicy({...policy,mode})}><ShieldCheck /><span><strong>{mode==='strict'?'Estricto':mode==='corporate'?'Corporativo':'Personalizado'}</strong><small>{mode==='strict'?'Bloquea cualquier dato sensible':mode==='corporate'?'Equilibrio entre seguridad y productividad':'Reglas adaptadas a tu organización'}</small></span></button>)}</Card><Card className="platform-card policy-rules"><h2>Reglas activas</h2>{Object.entries(policy?.rules ?? {}).map(([key,value]) => <div key={key}><span>{key.replace('_',' ')}</span><b>{String(value)}</b></div>)}<Button onClick={() => void save()}><Save /> Guardar política</Button>{saved && <small className="saved-note">Versión {policy?.version} publicada</small>}</Card></div></>
}

export function SecurityLabPage() {
  const [items,setItems] = useState<Scenario[]>([]); const [copied,setCopied] = useState('')
  useEffect(() => { void request<Scenario[]>('/api/v1/platform/lab/scenarios').then(setItems) }, [])
  const copy = async (item:Scenario) => { await navigator.clipboard.writeText(item.sample); setCopied(item.id) }
  return <><PageHeading eyebrow="Attack lab" title="Laboratorio" description="Escenarios seguros para demostrar cómo responde el perímetro." /><div className="scenario-grid">{items.map(item => <Card className="scenario-card" key={item.id}><div><FlaskConical /><span className={`scenario-risk scenario-risk--${item.risk}`}>{item.risk}</span></div><h2>{item.name}</h2><code>{item.sample}</code><Button variant="outline" onClick={() => void copy(item)}><Clipboard />{copied===item.id?'Copiado':'Copiar escenario'}</Button></Card>)}</div></>
}
