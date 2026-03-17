'use client'

import { use } from 'react'
import Link from 'next/link'
import { ArrowLeft, FileText, Layers, Briefcase, GraduationCap, Code2 } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getResumeByIdApi, getResumeVersionsApi } from '@/api/resumes'
import { QUERY_KEYS } from '@/lib/constants'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { PageLoader } from '@/components/common/loading-spinner'
import { formatDate } from '@/lib/utils'

export default function ResumeDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { data: resume, isLoading } = useQuery({
    queryKey: [QUERY_KEYS.RESUME, id],
    queryFn: () => getResumeByIdApi(id),
    enabled: !!id,
  })
  const { data: versions } = useQuery({
    queryKey: [QUERY_KEYS.RESUME_VERSIONS, id],
    queryFn: () => getResumeVersionsApi(id),
    enabled: !!id,
  })

  if (isLoading) return <PageLoader />
  if (!resume) return (
    <div className="text-center py-20 text-muted-foreground">Resume not found</div>
  )

  const parsed = resume.parsed_data

  return (
    <div className="space-y-6 max-w-4xl">
      <Button asChild variant="ghost" size="sm" className="gap-2 text-muted-foreground">
        <Link href="/resumes">
          <ArrowLeft className="w-4 h-4" />
          Back to Resumes
        </Link>
      </Button>

      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
          <FileText className="w-6 h-6 text-primary" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">{resume.name}</h1>
            {resume.is_active && (
              <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/30">Active</Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Uploaded {formatDate(resume.created_at)} · {versions?.length || 0} tailored versions
          </p>
        </div>
      </div>

      <Tabs defaultValue="parsed">
        <TabsList>
          <TabsTrigger value="parsed">Parsed Content</TabsTrigger>
          <TabsTrigger value="versions">
            Tailored Versions ({versions?.length || 0})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="parsed" className="space-y-4">
          {/* Summary */}
          {parsed?.summary && (
            <Card>
              <CardHeader><CardTitle className="text-base">Summary</CardTitle></CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground leading-relaxed">{parsed.summary}</p>
              </CardContent>
            </Card>
          )}

          {/* Skills */}
          {parsed?.skills && parsed.skills.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Code2 className="w-4 h-4 text-primary" />
                  <CardTitle className="text-base">Skills ({parsed.skills.length})</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {parsed.skills.map((skill) => (
                    <Badge key={skill} variant="outline" className="text-xs">{skill}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Experience */}
          {parsed?.experience && parsed.experience.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-primary" />
                  <CardTitle className="text-base">Experience</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {parsed.experience.map((exp, i) => (
                  <div key={i}>
                    {i > 0 && <Separator className="mb-6" />}
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h4 className="font-semibold text-foreground">{exp.title}</h4>
                        <p className="text-sm text-primary">{exp.company}</p>
                        {exp.location && (
                          <p className="text-xs text-muted-foreground">{exp.location}</p>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground whitespace-nowrap">
                        {exp.start_date} – {exp.is_current ? 'Present' : (exp.end_date || '?')}
                      </p>
                    </div>
                    <p className="text-sm text-muted-foreground mt-2 leading-relaxed">{exp.description}</p>
                    {exp.achievements.length > 0 && (
                      <ul className="mt-2 space-y-1">
                        {exp.achievements.map((a, j) => (
                          <li key={j} className="flex items-start gap-2 text-xs text-muted-foreground">
                            <div className="w-1.5 h-1.5 rounded-full bg-primary shrink-0 mt-1.5" />
                            {a}
                          </li>
                        ))}
                      </ul>
                    )}
                    {exp.technologies.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {exp.technologies.map((t) => (
                          <span key={t} className="text-[11px] px-2 py-0.5 rounded-md bg-muted text-muted-foreground">
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Education */}
          {parsed?.education && parsed.education.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <GraduationCap className="w-4 h-4 text-primary" />
                  <CardTitle className="text-base">Education</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {parsed.education.map((edu, i) => (
                  <div key={i} className="flex items-start justify-between gap-4">
                    <div>
                      <h4 className="font-semibold text-foreground">{edu.institution}</h4>
                      <p className="text-sm text-muted-foreground">
                        {edu.degree} in {edu.field}
                      </p>
                      {edu.gpa && (
                        <p className="text-xs text-muted-foreground">GPA: {edu.gpa}</p>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground whitespace-nowrap">
                      {edu.start_date} – {edu.end_date || 'Present'}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="versions">
          {!versions || versions.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Layers className="w-8 h-8 mx-auto mb-3 opacity-40" />
              <p className="text-sm">No tailored versions yet.</p>
              <p className="text-xs mt-1">Apply to a job to create a tailored version.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {versions.map((version) => (
                <Card key={version.id}>
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                      <Layers className="w-4 h-4 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-foreground">{version.name}</h4>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Created {formatDate(version.created_at)} · {version.ai_model_used || 'AI'}
                      </p>
                      {version.tailoring_strategy.keywords_added.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {version.tailoring_strategy.keywords_added.slice(0, 4).map((k) => (
                            <span
                              key={k}
                              className="text-[10px] px-1.5 py-0.5 rounded-md bg-primary/10 text-primary"
                            >
                              +{k}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    {version.pdf_url && (
                      <Button asChild size="sm" variant="outline">
                        <a href={version.pdf_url} target="_blank" rel="noopener noreferrer">
                          Download PDF
                        </a>
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
