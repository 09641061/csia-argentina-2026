import { request } from '@/shared/infrastructure/api/http-client'
import type { HealthResource } from '@/shared/infrastructure/api/resources'

export interface SystemHealth {
  readonly ready: boolean
  readonly database: boolean
  readonly securityModel: boolean
  readonly discoveryModel: boolean
  readonly generationModel: boolean
  readonly visionModel: boolean
  readonly models: readonly string[]
}

export async function getSystemHealth(signal?: AbortSignal): Promise<SystemHealth> {
  const resource = await request<HealthResource>('/api/v1/health', {
    signal,
    timeoutMs: 8_000,
    authenticated: false,
  })
  return {
    ready: resource.status === 'ok',
    database: resource.database,
    securityModel: resource.security_model_available,
    discoveryModel: resource.discovery_model_available,
    generationModel: resource.generation_model_available,
    visionModel: resource.vision_model_available,
    models: [resource.security_model, resource.discovery_model, resource.generation_model, resource.vision_model],
  }
}

