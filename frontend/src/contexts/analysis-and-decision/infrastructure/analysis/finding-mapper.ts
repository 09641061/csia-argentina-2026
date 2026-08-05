import {
  FINDING_SEVERITIES,
  type Finding,
  type FindingOrigin,
  type FindingSeverity,
} from '@/contexts/analysis-and-decision/domain/analysis/finding'
import type {
  AnalysisFindingResource,
  MaskedFindingResource,
} from '@/shared/infrastructure/api/resources'

export function toFinding(resource: MaskedFindingResource): Finding {
  return {
    origin: toOrigin(resource.origin),
    findingType: resource.finding_type,
    severity: toSeverity(resource.severity),
    title: resource.title,
    location: resource.location,
    maskedEvidence: resource.masked_evidence,
    occurrences: resource.occurrences,
    isPlaceholder: resource.is_placeholder,
  }
}

export function toFindingFromAnalysis(
  resource: AnalysisFindingResource,
  origin: FindingOrigin,
): Finding {
  return {
    origin,
    findingType: resource.finding_type,
    severity: toSeverity(resource.severity),
    title: resource.title,
    location: resource.json_path,
    maskedEvidence: resource.evidence,
    occurrences: resource.occurrences,
    isPlaceholder: resource.is_placeholder,
  }
}

function toOrigin(value: string): FindingOrigin {
  return value === 'prompt' ? 'prompt' : 'document'
}

function toSeverity(value: string): FindingSeverity {
  return (FINDING_SEVERITIES as readonly string[]).includes(value)
    ? (value as FindingSeverity)
    : 'medium'
}
