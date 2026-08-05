import type { ReactNode } from 'react'

import { ClaudeSpark, ClaudeWordmark } from '@/shared/interfaces/components/claude-brand'

export function AuthShell({ children }: { readonly children: ReactNode }) {
  return (
    <main className="grid min-h-svh bg-[#1b1b1a] lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative hidden overflow-hidden border-r border-white/[0.07] bg-[#151514] px-12 py-10 lg:flex lg:flex-col xl:px-16">
        <ClaudeWordmark className="w-[126px]" />

        <div className="my-auto max-w-xl">
          <ClaudeSpark className="mb-8 size-12" />
          <h1 className="font-serif text-5xl font-normal leading-[1.08] tracking-[-0.035em] text-[#d4d1c8] xl:text-6xl">
            Consulta con IA sin perder el control del contenido.
          </h1>
          <p className="mt-6 max-w-lg text-[15px] leading-7 text-[#96958d]">
            Sentinel revisa cada consulta y archivo antes de permitir que el modelo local genere
            una respuesta.
          </p>
        </div>

        <p className="text-xs text-[#6f6e68]">Sentinel AI Guard · Acceso local protegido</p>
      </section>
      <section className="relative flex items-center justify-center px-5 py-12 sm:px-8">
        <div className="absolute left-5 top-6 lg:hidden">
          <ClaudeWordmark className="w-[108px]" />
        </div>
        {children}
      </section>
    </main>
  )
}
