import { Inbox } from 'lucide-react'

import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from '@/shared/interfaces/ui/empty'

interface EmptyStateProps {
  readonly title: string
  readonly description: string
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <Empty className="rounded-[22px] border border-white/[0.08] bg-[#242422]">
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <Inbox aria-hidden="true" />
        </EmptyMedia>
        <EmptyTitle>{title}</EmptyTitle>
        <EmptyDescription>{description}</EmptyDescription>
      </EmptyHeader>
    </Empty>
  )
}
