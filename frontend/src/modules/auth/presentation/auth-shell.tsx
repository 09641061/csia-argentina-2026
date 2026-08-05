import { ShieldCheck } from 'lucide-react'
import type { ReactNode } from 'react'

export function AuthShell({ children }: { readonly children: ReactNode }) {
  return (
    <main className="grid min-h-svh bg-background lg:grid-cols-2">
      <section className="hidden bg-primary px-12 py-10 text-primary-foreground lg:flex lg:flex-col">
        <div className="flex items-center gap-3 text-sm font-semibold tracking-wide">
          <span className="grid size-10 place-items-center rounded-lg border border-primary-foreground/20 [&_svg]:size-5">
            <ShieldCheck aria-hidden="true" />
          </span>
          SENTINEL AI GUARD
        </div>

        <div className="my-auto max-w-xl">
          <h1 className="text-4xl font-semibold tracking-tight text-balance xl:text-5xl">
            Consulta con IA sin perder el control del contenido.
          </h1>
          <p className="mt-5 max-w-lg text-base leading-7 text-primary-foreground/70">
            Cada consulta y archivo admitido se revisa antes de que el modelo genere una
            respuesta.
          </p>
        </div>
      </section>
      <section className="flex items-center justify-center px-5 py-10 sm:px-8">{children}</section>
    </main>
  )
}
