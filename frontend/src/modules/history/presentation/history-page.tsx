import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

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
    <>
      <h1 className="page-title">Historial</h1>
      <p className="page-lead">
        Cada consulta revisada, con su decisión y la explicación de por qué se permitió o se
        bloqueó.
      </p>

      {isLoading && <LoadingStatus message="Cargando el historial…" />}

      {errorMessage && !isLoading && <ErrorNotice message={errorMessage} onRetry={retry} />}

      {page && !isLoading && page.items.length === 0 && (
        <EmptyState
          title="Todavía no hay consultas"
          description="Cuando envíes tu primera consulta aparecerá aquí junto con su decisión."
        />
      )}

      {page && !isLoading && page.items.length > 0 && (
        <>
          <div className="table-scroll">
            <table className="table">
              <caption className="visually-hidden">Consultas revisadas por Sentinel</caption>
              <thead>
                <tr>
                  <th scope="col">Tipo</th>
                  <th scope="col">Referencia</th>
                  <th scope="col">Fecha</th>
                  <th scope="col">Riesgo</th>
                  <th scope="col">Decisión</th>
                  <th scope="col">Generación</th>
                  <th scope="col">
                    <span className="visually-hidden">Acciones</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {page.items.map((interaction) => (
                  <tr key={interaction.id}>
                    <td>{contentTypeLabel(interaction.contentType)}</td>
                    <td className="table__reference">{interaction.contentReference}</td>
                    <td className="table__date">{formatDateTime(interaction.createdAt)}</td>
                    <td>
                      <RiskLabel risk={interaction.riskLevel} />
                    </td>
                    <td className={`decision--${interaction.decision}`}>
                      {decisionLabel(interaction.decision).replace('Consulta ', '')}
                    </td>
                    <td>{generationStatusLabel(interaction.generationStatus)}</td>
                    <td>
                      <Link to={`/historial/${interaction.id}`}>Ver detalle</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <span>
              Página {page.page} de {totalPages(page)} · {page.total}{' '}
              {page.total === 1 ? 'consulta' : 'consultas'}
            </span>
            <span className="pagination__buttons">
              <button
                type="button"
                className="button button--secondary"
                onClick={() => goToPage(currentPage - 1)}
                disabled={currentPage <= 1}
              >
                Anterior
              </button>
              <button
                type="button"
                className="button button--secondary"
                onClick={() => goToPage(currentPage + 1)}
                disabled={currentPage >= totalPages(page)}
              >
                Siguiente
              </button>
            </span>
          </div>
        </>
      )}
    </>
  )
}
