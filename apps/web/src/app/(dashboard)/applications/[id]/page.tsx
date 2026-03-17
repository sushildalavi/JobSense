'use client'

import { use } from 'react'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { useApplication, useApplicationEvents } from '@/hooks/use-applications'
import { ApplicationDetail } from '@/components/applications/application-detail'
import { Button } from '@/components/ui/button'
import { PageLoader } from '@/components/common/loading-spinner'

export default function ApplicationDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { data: application, isLoading } = useApplication(id)
  const { data: events } = useApplicationEvents(id)

  if (isLoading) return <PageLoader />
  if (!application) {
    return (
      <div className="text-center py-20">
        <p className="text-muted-foreground">Application not found</p>
        <Button asChild variant="link" className="mt-4">
          <Link href="/applications">Back to Applications</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="gap-2 text-muted-foreground">
        <Link href="/applications">
          <ArrowLeft className="w-4 h-4" />
          Back to Applications
        </Link>
      </Button>

      <ApplicationDetail application={application} events={events} />
    </div>
  )
}
