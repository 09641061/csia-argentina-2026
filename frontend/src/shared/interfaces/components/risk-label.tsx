import { Badge } from '@/shared/interfaces/ui/badge'

type RiskLevel = 'low' | 'medium' | 'high' | 'critical'

const LABELS: Record<RiskLevel, string> = {
  low: 'Riesgo bajo',
  medium: 'Riesgo medio',
  high: 'Riesgo alto',
  critical: 'Riesgo crítico',
}

interface RiskLabelProps {
  readonly risk: RiskLevel | null
}

export function RiskLabel({ risk }: RiskLabelProps) {
  const styles: Partial<Record<RiskLevel, string>> = {
    low: 'border-[#4b6653] bg-[#2a372e] text-[#abd0b4]',
    medium: 'border-[#71603d] bg-[#3a3324] text-[#dfc07d]',
    high: 'border-[#7e4a3f] bg-[#3b2925] text-[#eda08b]',
    critical: 'border-[#8a4040] bg-[#3d2424] text-[#f09b9b]',
  }
  const style = risk ? styles[risk] : undefined

  return (
    <Badge variant="outline" className={style ?? 'border-white/10 bg-transparent text-[#aaa89f]'}>
      {risk === null ? 'Riesgo no verificado' : LABELS[risk]}
    </Badge>
  )
}
