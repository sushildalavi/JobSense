'use client'

import { motion } from 'framer-motion'
import { MapPin, Bookmark, ExternalLink, Building2, Clock } from 'lucide-react'
import Link from 'next/link'
import type { JobListItem } from '@applyflow/types'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { MatchScoreRing } from './match-score-ring'
import { useShortlistJob } from '@/hooks/use-jobs'
import { formatDate, capitalize } from '@/lib/utils'

interface JobCardProps {
  job: JobListItem
}

export function JobCard({ job }: JobCardProps) {
  const { mutate: shortlist, isPending } = useShortlistJob()

  return (
    <motion.div
      whileHover={{ y: -2, scale: 1.01 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="group hover:border-primary/30 hover:shadow-glow-sm transition-all duration-300 h-full">
        <CardContent className="p-5">
          {/* Header */}
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500/20 to-violet-500/20 border border-border flex items-center justify-center shrink-0">
                <Building2 className="w-5 h-5 text-muted-foreground" />
              </div>
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground truncate">{job.company_name}</p>
                <h3 className="font-semibold text-foreground text-sm leading-snug line-clamp-2 group-hover:text-primary transition-colors">
                  {job.title}
                </h3>
              </div>
            </div>
            {job.match_score !== undefined && (
              <MatchScoreRing score={Math.round(job.match_score)} size={44} strokeWidth={3} />
            )}
          </div>

          {/* Location */}
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-3">
            <MapPin className="w-3 h-3 shrink-0" />
            <span className="truncate">{job.location}</span>
            {job.is_remote && (
              <Badge variant="success" className="text-[10px] py-0 px-1.5 ml-1">Remote</Badge>
            )}
          </div>

          {/* Badges */}
          <div className="flex flex-wrap gap-1.5 mb-4">
            <Badge variant="outline" className="text-[11px] py-0 px-2">
              {capitalize(job.employment_type)}
            </Badge>
            <Badge variant="outline" className="text-[11px] py-0 px-2">
              {capitalize(job.seniority)}
            </Badge>
            {job.salary_text && (
              <Badge variant="muted" className="text-[11px] py-0 px-2">
                {job.salary_text}
              </Badge>
            )}
          </div>

          {/* Date */}
          <div className="flex items-center gap-1 text-xs text-muted-foreground mb-4">
            <Clock className="w-3 h-3" />
            <span>{formatDate(job.posting_date || job.created_at, 'MMM d')}</span>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <Button asChild size="sm" variant="outline" className="flex-1 text-xs">
              <Link href={`/jobs/${job.id}`}>View Details</Link>
            </Button>
            <Button
              size="icon-sm"
              variant="ghost"
              onClick={() => shortlist(job.id)}
              disabled={isPending}
              className="text-muted-foreground hover:text-primary"
            >
              <Bookmark className="w-4 h-4" />
            </Button>
            <Button
              size="icon-sm"
              variant="ghost"
              asChild
              className="text-muted-foreground hover:text-foreground"
            >
              <a href={job.apply_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="w-4 h-4" />
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
