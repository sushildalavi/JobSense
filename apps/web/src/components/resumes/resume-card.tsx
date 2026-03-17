'use client'

import { FileText, Star, Trash2, Eye, Layers } from 'lucide-react'
import Link from 'next/link'
import type { MasterResume } from '@applyflow/types'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatRelativeDate } from '@/lib/utils'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deleteResumeApi, setActiveResumeApi } from '@/api/resumes'
import { QUERY_KEYS } from '@/lib/constants'
import { toast } from 'sonner'

interface ResumeCardProps {
  resume: MasterResume
  versionsCount?: number
}

export function ResumeCard({ resume, versionsCount = 0 }: ResumeCardProps) {
  const queryClient = useQueryClient()

  const { mutate: deleteResume } = useMutation({
    mutationFn: () => deleteResumeApi(resume.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.RESUMES] })
      toast.success('Resume deleted')
    },
    onError: () => toast.error('Failed to delete resume'),
  })

  const { mutate: setActive } = useMutation({
    mutationFn: () => setActiveResumeApi(resume.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.RESUMES] })
      toast.success('Set as active resume')
    },
    onError: () => toast.error('Failed to update resume'),
  })

  return (
    <Card className="group hover:border-primary/30 transition-all">
      <CardContent className="p-5">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
            <FileText className="w-5 h-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold text-foreground truncate">{resume.name}</h3>
              {resume.is_active && (
                <Badge className="text-[10px] py-0 px-2 bg-emerald-500/20 text-emerald-300 border-emerald-500/30">
                  Active
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Updated {formatRelativeDate(resume.created_at)}
            </p>
            <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
              {resume.parsed_data?.skills?.length > 0 && (
                <span>{resume.parsed_data.skills.length} skills</span>
              )}
              {resume.parsed_data?.experience?.length > 0 && (
                <span>{resume.parsed_data.experience.length} roles</span>
              )}
              {versionsCount > 0 && (
                <span className="flex items-center gap-1">
                  <Layers className="w-3 h-3" />
                  {versionsCount} tailored versions
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-4">
          <Button asChild size="sm" variant="outline" className="flex-1 text-xs">
            <Link href={`/resumes/${resume.id}`}>
              <Eye className="w-3.5 h-3.5 mr-1.5" />
              View
            </Link>
          </Button>
          {!resume.is_active && (
            <Button
              size="sm"
              variant="ghost"
              className="text-xs"
              onClick={() => setActive()}
            >
              <Star className="w-3.5 h-3.5 mr-1.5" />
              Set Active
            </Button>
          )}
          <Button
            size="icon-sm"
            variant="ghost"
            className="text-muted-foreground hover:text-destructive"
            onClick={() => deleteResume()}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
