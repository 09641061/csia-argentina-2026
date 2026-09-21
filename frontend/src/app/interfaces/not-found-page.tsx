import { Link } from 'react-router-dom'

import { ClaudeSpark } from '@/shared/interfaces/components/claude-brand'
import { Button } from '@/shared/interfaces/ui/button'

export function NotFoundPage() {
  return (
    <section className="mx-auto flex min-h-full max-w-lg flex-col items-center justify-center px-5 text-center">
      <ClaudeSpark className="mb-6 size-11" />
      <span className="text-xs font-medium uppercase tracking-[0.18em] text-[#77766f]">404</span>
      <h1 className="mt-3 font-serif text-4xl font-normal tracking-[-0.03em] text-[#d8d5cd]">
        Página no encontrada
      </h1>
      <p className="mt-3 text-sm leading-6 text-[#96958d]">
        La dirección que abriste no existe en Claude AI Guard.
      </p>
      <Button
        asChild
        variant="secondary"
        className="mt-7 rounded-xl bg-[#eceae3] text-[#222220] hover:bg-white"
      >
        <Link to="/">Ir a Consultar</Link>
      </Button>
    </section>
  )
}
