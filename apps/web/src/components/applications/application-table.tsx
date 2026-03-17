'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowUpDown, Trash2, Eye } from 'lucide-react'
import type { ApplicationListItem, ApplicationStatus } from '@applyflow/types'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { StatusBadge } from './status-badge'
import { formatDate } from '@/lib/utils'
import { useDeleteApplication } from '@/hooks/use-applications'
import { STATUS_LABELS } from '@/lib/constants'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'

interface ApplicationTableProps {
  applications: ApplicationListItem[]
  isLoading?: boolean
}

type SortField = 'company_name' | 'status' | 'applied_at' | 'created_at'

const tabFilters: { label: string; statuses: ApplicationStatus[] | 'all' }[] = [
  { label: 'All', statuses: 'all' },
  {
    label: 'Active',
    statuses: ['shortlisted', 'tailored', 'ready_to_apply', 'applied', 'oa_received', 'recruiter_contacted'],
  },
  { label: 'Interviewing', statuses: ['interview_scheduled'] },
  { label: 'Closed', statuses: ['rejected', 'offer', 'archived'] },
]

export function ApplicationTable({ applications, isLoading }: ApplicationTableProps) {
  const [sortField, setSortField] = useState<SortField>('created_at')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [activeTab, setActiveTab] = useState('All')
  const { mutate: deleteApp } = useDeleteApplication()

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortDir('desc')
    }
  }

  const filtered = applications.filter((app) => {
    const tab = tabFilters.find((t) => t.label === activeTab)
    if (!tab || tab.statuses === 'all') return true
    return (tab.statuses as ApplicationStatus[]).includes(app.status)
  })

  const sorted = [...filtered].sort((a, b) => {
    let aVal = a[sortField] || ''
    let bVal = b[sortField] || ''
    if (sortDir === 'desc') [aVal, bVal] = [bVal, aVal]
    return aVal < bVal ? -1 : aVal > bVal ? 1 : 0
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          {tabFilters.map((t) => (
            <TabsTrigger key={t.label} value={t.label}>
              {t.label}
              <span className="ml-1.5 text-xs bg-muted px-1.5 py-0.5 rounded-full">
                {
                  t.statuses === 'all'
                    ? applications.length
                    : applications.filter((a) => (t.statuses as ApplicationStatus[]).includes(a.status)).length
                }
              </span>
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <div className="rounded-xl border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[200px]">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 text-muted-foreground font-medium hover:text-foreground"
                  onClick={() => handleSort('company_name')}
                >
                  Company
                  <ArrowUpDown className="ml-1 h-3 w-3" />
                </Button>
              </TableHead>
              <TableHead>Role</TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 text-muted-foreground font-medium hover:text-foreground"
                  onClick={() => handleSort('status')}
                >
                  Status
                  <ArrowUpDown className="ml-1 h-3 w-3" />
                </Button>
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 text-muted-foreground font-medium hover:text-foreground"
                  onClick={() => handleSort('applied_at')}
                >
                  Applied
                  <ArrowUpDown className="ml-1 h-3 w-3" />
                </Button>
              </TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-12 text-muted-foreground">
                  No applications found
                </TableCell>
              </TableRow>
            ) : (
              sorted.map((app) => (
                <TableRow key={app.id}>
                  <TableCell>
                    <span className="font-medium text-foreground">{app.company_name}</span>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-muted-foreground">{app.job_title}</span>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={app.status} />
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-muted-foreground">
                      {formatDate(app.applied_at || app.created_at)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center justify-end gap-1">
                      <Button asChild size="icon-sm" variant="ghost">
                        <Link href={`/applications/${app.id}`}>
                          <Eye className="w-4 h-4" />
                        </Link>
                      </Button>
                      <Button
                        size="icon-sm"
                        variant="ghost"
                        className="text-muted-foreground hover:text-destructive"
                        onClick={() => deleteApp(app.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
