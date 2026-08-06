import { ShieldCheck, ShieldEllipsis, ShieldX } from 'lucide-react'
import { useEffect, useState } from 'react'

import { getSystemHealth, type SystemHealth } from '@/shared/infrastructure/api/http-health-service'

export function SystemHealthStatus() {
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [unavailable, setUnavailable] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    getSystemHealth(controller.signal).then(setHealth).catch(() => { if (!controller.signal.aborted) setUnavailable(true) })
    return () => controller.abort()
  }, [])

  const ready = health?.ready === true
  const Icon = unavailable ? ShieldX : health === null ? ShieldEllipsis : ready ? ShieldCheck : ShieldX
  const label = unavailable ? 'Backend no disponible' : health === null ? 'Comprobando servicios' : ready ? 'Protección local activa' : 'Servicios locales degradados'

  return <span className={`relative grid size-8 place-items-center rounded-lg ${ready ? 'text-[#b7c9b8]' : unavailable || health ? 'text-[#d48b78]' : 'text-[#8e8c84]'}`} aria-label={label} title={health ? `${label}. Base de datos y ${health.models.length} modelos verificados.` : label}><Icon className="size-[18px]" aria-hidden="true" /><span className={`absolute right-0 top-0 size-2 rounded-full border-2 border-[#151514] ${ready ? 'bg-[#73a77c]' : health || unavailable ? 'bg-[#d97757]' : 'bg-[#77766f]'}`} /></span>
}
