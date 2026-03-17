'use client'

import { use } from 'react'
import Link from 'next/link'
import {
  ArrowLeft,
  MapPin,
  ExternalLink,
  Bookmark,
  CheckCircle2,
  XCircle,
  Building2,
  Briefcase,
  Clock,
} from 'lucide-react'
import { useJob, useShortlistJob } from '@/hooks/use-jobs'
import { useCreateApplication } from '@/hooks/use-applications'
import { MatchScoreRing } from '@/components/jobs/match-score-ring'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { PageLoader } from '@/components/common/loading-spinner'
import { formatDate, formatSalary, capitalize } from '@/lib/utils'


export default function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { data: job, isLoading } = useJob(id)
  const { mutate: shortlist, isPending: shortlisting } = useShortlistJob()
  const { mutate: createApp, isPending: applying } = useCreateApplication()

  if (isLoading) return <PageLoader />
  if (!job) return (
    <div className="text-center py-20 text-muted-foreground">Job not found</div>
  )

  const match = job.match

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Back + actions */}
      <div className="flex items-center justify-between gap-4">
        <Button asChild variant="ghost" size="sm" className="gap-2 text-muted-foreground">
          <Link href="/jobs">
            <ArrowLeft className="w-4 h-4" />
            Back to Jobs
          </Link>
        </Button>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => shortlist(job.id)}
            disabled={shortlisting}
            className="gap-2"
          >
            <Bookmark className="w-4 h-4" />
            Shortlist
          </Button>
          <Button
            size="sm"
            onClick={() => createApp({ job_id: job.id })}
            disabled={applying}
            loading={applying}
            className="gap-2"
          >
            Apply Now
          </Button>
        </div>
      </div>

      {/* Hero card */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start gap-5">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-indigo-500/20 to-violet-500/20 border border-border flex items-center justify-center shrink-0">
              <Building2 className="w-7 h-7 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h1 className="text-2xl font-bold text-foreground">{job.title}</h1>
                  <p className="text-lg text-muted-foreground mt-1">{job.company_name}</p>
                </div>
                {match && (
                  <div className="text-center shrink-0">
                    <MatchScoreRing score={Math.round(match.match_score)} size={72} strokeWidth={5} />
                    <p className="text-xs text-muted-foreground mt-1">Match</p>
                  </div>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-3 mt-4">
                {job.is_remote && <Badge variant="success">Remote</Badge>}
                {job.is_hybrid && <Badge variant="warning">Hybrid</Badge>}
                <span className="flex items-center gap-1 text-sm text-muted-foreground">
                  <MapPin className="w-3.5 h-3.5" />
                  {job.location}
                </span>
                <span className="flex items-center gap-1 text-sm text-muted-foreground">
                  <Briefcase className="w-3.5 h-3.5" />
                  {capitalize(job.employment_type)} · {capitalize(job.seniority)}
                </span>
                {(job.salary_min || job.salary_max || job.salary_text) && (
                  <span className="text-sm text-emerald-400 font-medium">
                    {formatSalary(job.salary_min, job.salary_max, job.currency, job.salary_text)}
                  </span>
                )}
                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="w-3 h-3" />
                  {formatDate(job.posting_date || job.created_at)}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="requirements">Requirements</TabsTrigger>
          {match && <TabsTrigger value="match">Match Analysis</TabsTrigger>}
        </TabsList>

        <TabsContent value="overview">
          <Card>
            <CardContent className="p-6 prose prose-invert max-w-none">
              <div
                className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap"
                dangerouslySetInnerHTML={{ __html: job.cleaned_description.replace(/\n/g, '<br/>') }}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="requirements">
          <div className="space-y-4">
            {job.requirements.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Requirements</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {job.requirements.map((req, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                        <span className="text-muted-foreground">{req}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {job.preferred_qualifications.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Preferred Qualifications</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {job.preferred_qualifications.map((q, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <div className="w-4 h-4 rounded-full border border-primary/50 shrink-0 mt-0.5" />
                        <span className="text-muted-foreground">{q}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {job.responsibilities.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Responsibilities</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {job.responsibilities.map((r, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <div className="w-1.5 h-1.5 rounded-full bg-primary shrink-0 mt-2" />
                        <span className="text-muted-foreground">{r}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {match && (
          <TabsContent value="match">
            <div className="space-y-4">
              {/* Explanation */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Match Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-6 mb-4">
                    <MatchScoreRing score={Math.round(match.match_score)} size={80} strokeWidth={6} />
                    <p className="text-sm text-muted-foreground leading-relaxed flex-1">
                      {match.explanation}
                    </p>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-xs text-muted-foreground mb-1">
                        <span>Overall Score</span>
                        <span>{Math.round(match.match_score)}%</span>
                      </div>
                      <Progress value={match.match_score} />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Strengths */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base text-emerald-400">Matched Skills</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {match.skill_matches.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No matched skills</p>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {match.skill_matches.map((skill) => (
                          <span
                            key={skill}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                          >
                            <CheckCircle2 className="w-3 h-3" />
                            {skill}
                          </span>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base text-amber-400">Skill Gaps</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {match.skill_gaps.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No skill gaps identified</p>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {match.skill_gaps.map((skill) => (
                          <span
                            key={skill}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-amber-500/10 text-amber-300 border border-amber-500/20"
                          >
                            <XCircle className="w-3 h-3" />
                            {skill}
                          </span>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Strengths/Weaknesses */}
              {(match.strengths.length > 0 || match.weaknesses.length > 0) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {match.strengths.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Strengths</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-1.5">
                          {match.strengths.map((s, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                              {s}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}
                  {match.weaknesses.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Areas to Improve</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-1.5">
                          {match.weaknesses.map((w, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                              <XCircle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                              {w}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}
            </div>
          </TabsContent>
        )}
      </Tabs>

      {/* Apply CTA */}
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="p-6 flex items-center justify-between gap-4">
          <div>
            <h3 className="font-semibold text-foreground">Ready to apply?</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Let ApplyFlow tailor your resume and track this application.
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button asChild variant="outline" size="sm">
              <a href={job.apply_url} target="_blank" rel="noopener noreferrer" className="gap-2">
                <ExternalLink className="w-4 h-4" />
                Apply Directly
              </a>
            </Button>
            <Button
              size="sm"
              onClick={() => createApp({ job_id: job.id })}
              disabled={applying}
              loading={applying}
            >
              Track Application
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
