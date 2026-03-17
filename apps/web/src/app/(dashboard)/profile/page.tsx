'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  User,
  MapPin,
  Briefcase,
  DollarSign,
  Code2,
  Link2,
  Mail,
  Calendar,
  Plus,
  X,
} from 'lucide-react'
import apiClient from '@/lib/api'
import { API_ROUTES, QUERY_KEYS } from '@/lib/constants'
import type { Profile, RemotePreference, SeniorityLevel } from '@applyflow/types'
import { PageHeader } from '@/components/common/page-header'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { queryClient } from '@/lib/query-client'

const remoteOptions: { label: string; value: RemotePreference }[] = [
  { label: 'Remote Only', value: 'remote_only' },
  { label: 'Hybrid', value: 'hybrid' },
  { label: 'On-site', value: 'onsite' },
  { label: 'Flexible', value: 'flexible' },
]

export default function ProfilePage() {
  const { data: profile, isLoading } = useQuery<Profile>({
    queryKey: [QUERY_KEYS.PROFILE],
    queryFn: async () => {
      const res = await apiClient.get(API_ROUTES.PROFILE)
      return res.data
    },
  })

  const [skills, setSkills] = useState<string[]>([])
  const [skillInput, setSkillInput] = useState('')
  const [targetRoles, setTargetRoles] = useState<string[]>([])
  const [roleInput, setRoleInput] = useState('')

  useEffect(() => {
    if (profile) {
      setSkills(profile.skills || [])
      setTargetRoles(profile.target_roles || [])
    }
  }, [profile])

  const { mutate: saveProfile, isPending } = useMutation({
    mutationFn: async (data: Partial<Profile>) => {
      const res = await apiClient.patch(API_ROUTES.PROFILE, data)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.PROFILE] })
      toast.success('Profile saved')
    },
    onError: () => toast.error('Failed to save profile'),
  })

  const addSkill = () => {
    if (skillInput.trim() && !skills.includes(skillInput.trim())) {
      setSkills([...skills, skillInput.trim()])
      setSkillInput('')
    }
  }

  const addRole = () => {
    if (roleInput.trim() && !targetRoles.includes(roleInput.trim())) {
      setTargetRoles([...targetRoles, roleInput.trim()])
      setRoleInput('')
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-48" />
        {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-48" />)}
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <PageHeader
        title="Profile & Preferences"
        subtitle="Configure your job search preferences"
        action={
          <Button onClick={() => saveProfile({ skills, target_roles: targetRoles })} loading={isPending}>
            Save Changes
          </Button>
        }
      />

      {/* Target Roles */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-primary" />
            <CardTitle className="text-base">Target Roles</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={roleInput}
              onChange={(e) => setRoleInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addRole()}
              placeholder="e.g. Software Engineer"
              className="flex-1"
            />
            <Button onClick={addRole} size="sm" variant="outline">
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          {targetRoles.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {targetRoles.map((role) => (
                <span
                  key={role}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs bg-primary/10 text-primary border border-primary/20"
                >
                  {role}
                  <X
                    className="w-3 h-3 cursor-pointer hover:text-foreground"
                    onClick={() => setTargetRoles(targetRoles.filter((r) => r !== role))}
                  />
                </span>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Location Preferences */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-primary" />
            <CardTitle className="text-base">Location Preferences</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-sm mb-1.5 block">Remote Preference</Label>
            <Select
              defaultValue={profile?.remote_preference || 'flexible'}
              onValueChange={(v) => saveProfile({ remote_preference: v as RemotePreference })}
            >
              <SelectTrigger className="max-w-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {remoteOptions.map((o) => (
                  <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Salary */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-primary" />
            <CardTitle className="text-base">Compensation Expectations</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-sm mb-1.5 block">Minimum Salary</Label>
              <Input
                type="number"
                defaultValue={profile?.salary_min}
                placeholder="e.g. 80000"
                onBlur={(e) => saveProfile({ salary_min: Number(e.target.value) || undefined })}
              />
            </div>
            <div>
              <Label className="text-sm mb-1.5 block">Maximum Salary</Label>
              <Input
                type="number"
                defaultValue={profile?.salary_max}
                placeholder="e.g. 150000"
                onBlur={(e) => saveProfile({ salary_max: Number(e.target.value) || undefined })}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Skills */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-primary" />
            <CardTitle className="text-base">Skills ({skills.length})</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addSkill()}
              placeholder="e.g. Python, React, AWS"
              className="flex-1"
            />
            <Button onClick={addSkill} size="sm" variant="outline">
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          {skills.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {skills.map((skill) => (
                <Badge key={skill} variant="outline" className="gap-1 pr-1.5">
                  {skill}
                  <X
                    className="w-3 h-3 cursor-pointer hover:text-destructive"
                    onClick={() => setSkills(skills.filter((s) => s !== skill))}
                  />
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Integrations */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Link2 className="w-4 h-4 text-primary" />
            <CardTitle className="text-base">Integration Status</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center">
                <Mail className="w-4 h-4 text-red-400" />
              </div>
              <div>
                <p className="text-sm font-medium">Gmail</p>
                <p className="text-xs text-muted-foreground">
                  {profile?.gmail_connected ? 'Connected' : 'Not connected'}
                </p>
              </div>
            </div>
            <Badge
              className={profile?.gmail_connected
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                : 'bg-muted text-muted-foreground border-border'}
            >
              {profile?.gmail_connected ? 'Connected' : 'Disconnected'}
            </Badge>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Calendar className="w-4 h-4 text-blue-400" />
              </div>
              <div>
                <p className="text-sm font-medium">Google Calendar</p>
                <p className="text-xs text-muted-foreground">
                  {profile?.google_calendar_connected ? 'Connected' : 'Not connected'}
                </p>
              </div>
            </div>
            <Badge
              className={profile?.google_calendar_connected
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                : 'bg-muted text-muted-foreground border-border'}
            >
              {profile?.google_calendar_connected ? 'Connected' : 'Disconnected'}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={() => saveProfile({ skills, target_roles: targetRoles })} loading={isPending}>
          Save All Changes
        </Button>
      </div>
    </div>
  )
}
