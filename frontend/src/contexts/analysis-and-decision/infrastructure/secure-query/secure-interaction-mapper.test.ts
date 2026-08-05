import { describe, expect, it } from 'vitest'

import { allowedInteractionResource, blockedInteractionResource } from '@/test/builders'

import { toSecureInteraction } from './secure-interaction-mapper'

describe('secure interaction mapper', () => {
  it('maps the backend resource into the domain shape', () => {
    const interaction = toSecureInteraction(blockedInteractionResource())

    expect(interaction.decision).toBe('blocked')
    expect(interaction.riskLevel).toBe('high')
    expect(interaction.maskedFindings).toHaveLength(1)
    expect(interaction.maskedFindings[0].maskedEvidence).toBe('Sup*********23')
  })

  it('treats an unknown verdict as blocked instead of allowed', () => {
    const interaction = toSecureInteraction(
      allowedInteractionResource({ decision: 'something-new' }),
    )
    expect(interaction.decision).toBe('blocked')
  })

  it('never turns a missing risk level into low', () => {
    const interaction = toSecureInteraction(allowedInteractionResource({ risk_level: null }))
    expect(interaction.riskLevel).toBeNull()
  })
})
