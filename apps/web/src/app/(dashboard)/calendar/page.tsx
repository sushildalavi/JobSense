'use client'

import { useState } from 'react'
import { RefreshCw, Calendar, Video, MapPin, Plus, ExternalLink } from 'lucide-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { getCalendarEventsApi, syncCalendarApi } from '@/api/calendar'
import { QUERY_KEYS } from '@/lib/constants'
import type { CalendarEvent } from '@applyflow/types'
import { PageHeader } from '@/components/common/page-header'
import { EmptyState } from '@/components/common/empty-state'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { formatDate } from '@/lib/utils'
import { format, parseISO, isToday, isTomorrow, isThisWeek, addDays } from 'date-fns'
import { toast } from 'sonner'
import { queryClient } from '@/lib/query-client'
import { cn } from '@/lib/utils'

function groupEventsByDate(events: CalendarEvent[]) {
  const groups: Record<string, CalendarEvent[]> = {}
  events.forEach((event) => {
    const dateKey = event.start_datetime.split('T')[0]
    if (!groups[dateKey]) groups[dateKey] = []
    groups[dateKey].push(event)
  })
  return groups
}

function getDateLabel(dateStr: string) {
  const date = parseISO(dateStr)
  if (isToday(date)) return 'Today'
  if (isTomorrow(date)) return 'Tomorrow'
  return format(date, 'EEEE, MMMM d')
}

function getStatusColor(status: CalendarEvent['status']) {
  switch (status) {
    case 'confirmed': return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
    case 'pending': return 'bg-amber-500/20 text-amber-300 border-amber-500/30'
    case 'cancelled': return 'bg-red-500/20 text-red-300 border-red-500/30'
  }
}

export default function CalendarPage() {
  const { data: events, isLoading } = useQuery({
    queryKey: [QUERY_KEYS.CALENDAR_EVENTS],
    queryFn: getCalendarEventsApi,
  })

  const { mutate: syncCalendar, isPending: syncing } = useMutation({
    mutationFn: syncCalendarApi,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.CALENDAR_EVENTS] })
      toast.success(`Synced: ${data.events_synced} events`)
    },
    onError: () => toast.error('Failed to sync calendar'),
  })

  const grouped = groupEventsByDate(events || [])
  const sortedDates = Object.keys(grouped).sort()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Upcoming Interviews"
        subtitle="Your scheduled interviews and meetings"
        action={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => syncCalendar()} loading={syncing}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Sync Calendar
            </Button>
            <Button size="sm">
              <Plus className="w-4 h-4 mr-2" />
              Add Event
            </Button>
          </div>
        }
      />

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
      ) : !events || events.length === 0 ? (
        <EmptyState
          icon={Calendar}
          title="No upcoming interviews"
          description="Sync your Google Calendar or add events manually to track your interviews here."
          action={{ label: 'Sync Calendar', onClick: () => syncCalendar() }}
        />
      ) : (
        <div className="space-y-8">
          {sortedDates.map((dateKey) => (
            <div key={dateKey}>
              <div className="flex items-center gap-3 mb-4">
                <h2 className="text-base font-semibold text-foreground">
                  {getDateLabel(dateKey)}
                </h2>
                <div className="flex-1 h-px bg-border" />
                <span className="text-xs text-muted-foreground">
                  {format(parseISO(dateKey), 'MMM d, yyyy')}
                </span>
              </div>

              <div className="space-y-3">
                {grouped[dateKey].map((event) => (
                  <Card key={event.id} className="hover:border-primary/20 transition-all">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-4">
                        {/* Time block */}
                        <div className="w-16 shrink-0 text-center">
                          <p className="text-sm font-bold text-foreground">
                            {format(parseISO(event.start_datetime), 'h:mm')}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {format(parseISO(event.start_datetime), 'a')}
                          </p>
                        </div>

                        <div className="w-px bg-border self-stretch shrink-0" />

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <h3 className="font-semibold text-foreground">{event.title}</h3>
                              {event.description && (
                                <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                  {event.description}
                                </p>
                              )}
                            </div>
                            <span
                              className={cn(
                                'px-2 py-0.5 rounded-full text-xs font-semibold border shrink-0',
                                getStatusColor(event.status)
                              )}
                            >
                              {event.status}
                            </span>
                          </div>

                          <div className="flex items-center gap-4 mt-2 flex-wrap">
                            <span className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Calendar className="w-3 h-3" />
                              {format(parseISO(event.start_datetime), 'h:mm a')} –{' '}
                              {format(parseISO(event.end_datetime), 'h:mm a')}
                            </span>
                            {event.timezone && (
                              <span className="text-xs text-muted-foreground">{event.timezone}</span>
                            )}
                            {event.location && (
                              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                                <MapPin className="w-3 h-3" />
                                {event.location}
                              </span>
                            )}
                          </div>

                          {event.meeting_link && (
                            <Button asChild size="sm" variant="outline" className="mt-3 gap-2">
                              <a href={event.meeting_link} target="_blank" rel="noopener noreferrer">
                                <Video className="w-3.5 h-3.5" />
                                Join Meeting
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
