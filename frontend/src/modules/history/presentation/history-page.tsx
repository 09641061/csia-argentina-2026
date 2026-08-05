import { ArrowLeft, ArrowRight, Eye } from 'lucide-react'
import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { contentTypeLabel } from '@/modules/analysis/domain/content-type'
import { decisionLabel } from '@/modules/analysis/domain/decision'
import { generationStatusLabel } from '@/modules/analysis/domain/generation-status'
import { totalPages } from '@/modules/history/domain/interaction-repository'
import { HttpInteractionRepository } from '@/modules/history/infrastructure/http-interaction-repository'
import { formatDateTime } from '@/shared/lib/format'
import { EmptyState } from '@/shared/ui/empty-state'
import { ErrorNotice } from '@/shared/ui/error-notice'
import { LoadingStatus } from '@/shared/ui/loading-status'
import { RiskLabel } from '@/shared/ui/risk-label'

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
    <div className="flex flex-col gap-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-primary">Event explorer</p>
          <h1 className="page-heading">Historial de eventos</h1>
          <p className="page-description">
            Investigá la evidencia enmascarada, la severidad y la decisión aplicada a cada operación.
          </p>
        </div>
        {page && (
          <Badge variant="outline" className="bg-background">
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
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle className="text-base">Eventos normalizados</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Evento</TableHead>
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
                      <span className="block">EVT-{String(interaction.id).padStart(5, '0')}</span>
                      <span className="text-xs font-normal text-muted-foreground">{contentTypeLabel(interaction.contentType)}</span>
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
