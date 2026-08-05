import { ArrowLeft, ArrowRight, Eye } from 'lucide-react'
import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Badge } from '@/shared/interfaces/ui/badge'
import { Button } from '@/shared/interfaces/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/shared/interfaces/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/interfaces/ui/table'
import { contentTypeLabel } from '@/contexts/analysis-and-decision/domain/analysis/content-type'
import { decisionLabel } from '@/contexts/analysis-and-decision/domain/analysis/decision'
import { generationStatusLabel } from '@/contexts/analysis-and-decision/domain/analysis/generation-status'
import { totalPages } from '@/contexts/analysis-and-decision/domain/history/interaction-repository'
import { HttpInteractionRepository } from '@/contexts/analysis-and-decision/infrastructure/history/http-interaction-repository'
import { formatDateTime } from '@/shared/lib/format'
import { EmptyState } from '@/shared/interfaces/components/empty-state'
import { ErrorNotice } from '@/shared/interfaces/components/error-notice'
import { LoadingStatus } from '@/shared/interfaces/components/loading-status'
import { RiskLabel } from '@/shared/interfaces/components/risk-label'

import { useInteractionHistory } from './use-interaction-history'

export function HistoryPage() {
  const repository = useMemo(() => new HttpInteractionRepository(), [])
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedPage = Number.parseInt(searchParams.get('pagina') ?? '1', 10)
  const currentPage = Number.isFinite(requestedPage) && requestedPage >= 1 ? requestedPage : 1
  const { page, isLoading, errorMessage, retry } = useInteractionHistory(repository, currentPage)

  const goToPage = (next: number) => {
    setSearchParams(next === 1 ? {} : { pagina: String(next) })
  }

  return (
    <div className="mx-auto flex min-h-full w-full max-w-[1180px] flex-col gap-8 px-5 pb-16 pt-24 sm:px-8 lg:px-10">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="page-heading">Historial</h1>
          <p className="page-description">
            Cada consulta revisada conserva su decisión, riesgo y explicación enmascarada.
          </p>
        </div>
        {page && (
          <Badge variant="outline" className="border-white/10 bg-transparent text-[#aaa89f]">
            {page.total} {page.total === 1 ? 'consulta' : 'consultas'}
          </Badge>
        )}
      </header>

      {isLoading && <LoadingStatus message="Cargando el historial…" />}
      {errorMessage && !isLoading && <ErrorNotice message={errorMessage} onRetry={retry} />}
      {page && !isLoading && page.items.length === 0 && (
        <EmptyState
          title="Todavía no hay consultas"
          description="Cuando envíes tu primera consulta aparecerá aquí junto con su decisión."
        />
      )}

      {page && !isLoading && page.items.length > 0 && (
        <Card className="overflow-hidden rounded-[22px] border-white/[0.08] bg-[#242422] shadow-[0_18px_55px_rgba(0,0,0,0.2)]">
          <CardHeader>
            <CardTitle className="text-base font-medium text-[#e8e6df]">Interacciones revisadas</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Referencia</TableHead>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Riesgo</TableHead>
                  <TableHead>Decisión</TableHead>
                  <TableHead>Generación</TableHead>
                  <TableHead className="w-16">
                    <span className="sr-only">Acciones</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {page.items.map((interaction) => (
                  <TableRow key={interaction.id}>
                    <TableCell className="font-medium">
                      {contentTypeLabel(interaction.contentType)}
                    </TableCell>
                    <TableCell className="max-w-64 truncate text-muted-foreground">
                      {interaction.contentReference}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-muted-foreground">
                      {formatDateTime(interaction.createdAt)}
                    </TableCell>
                    <TableCell>
                      <RiskLabel risk={interaction.riskLevel} />
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={interaction.decision === 'allowed' ? 'secondary' : 'outline'}
                        className={
                          interaction.decision === 'allowed'
                            ? 'bg-[#2d3931] text-[#aed2b6]'
                            : 'border-[#70443c] bg-[#372824] text-[#e8a08c]'
                        }
                      >
                        {decisionLabel(interaction.decision).replace('Consulta ', '')}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {generationStatusLabel(interaction.generationStatus)}
                    </TableCell>
                    <TableCell>
                      <Button asChild size="icon" variant="ghost">
                        <Link to={`/historial/${interaction.id}`} aria-label="Ver detalle">
                          <Eye aria-hidden="true" />
                        </Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
          <CardFooter className="flex flex-wrap justify-between gap-3">
            <span className="text-sm text-muted-foreground">
              Página {page.page} de {totalPages(page)}
            </span>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => goToPage(currentPage - 1)}
                disabled={currentPage <= 1}
              >
                <ArrowLeft data-icon="inline-start" /> Anterior
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => goToPage(currentPage + 1)}
                disabled={currentPage >= totalPages(page)}
              >
                Siguiente <ArrowRight data-icon="inline-end" />
              </Button>
            </div>
          </CardFooter>
        </Card>
      )}
    </div>
  )
}
