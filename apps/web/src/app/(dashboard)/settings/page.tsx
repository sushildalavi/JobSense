'use client'

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  Settings,
  Mail,
  Calendar,
  Bell,
  Shield,
  Palette,
  Key,
  Trash2,
  Download,
  Check,
  X,
} from 'lucide-react'
import apiClient from '@/lib/api'
import { API_ROUTES, QUERY_KEYS } from '@/lib/constants'
import type { Profile } from '@jobsense/types'
import { PageHeader } from '@/components/common/page-header'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { queryClient } from '@/lib/query-client'

export default function SettingsPage() {
  const [apifyKey, setApifyKey] = useState('')
  const [openaiKey, setOpenaiKey] = useState('')

  const { data: profile, isLoading } = useQuery<Profile>({
    queryKey: [QUERY_KEYS.PROFILE],
    queryFn: async () => {
      const res = await apiClient.get(API_ROUTES.PROFILE)
      return res.data
    },
  })

  const { mutate: updateProfile, isPending } = useMutation({
    mutationFn: async (data: Partial<Profile>) => {
      const res = await apiClient.patch(API_ROUTES.PROFILE, data)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.PROFILE] })
      toast.success('Settings saved')
    },
    onError: () => toast.error('Failed to save settings'),
  })

  return (
    <div className="space-y-6 max-w-3xl">
      <PageHeader
        title="Settings"
        subtitle="Manage your account and preferences"
      />

      <Tabs defaultValue="general">
        <TabsList className="grid grid-cols-4 w-full">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="integrations">Integrations</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="account">Account</TabsTrigger>
        </TabsList>

        {/* General */}
        <TabsContent value="general" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Palette className="w-4 h-4 text-primary" />
                <CardTitle className="text-base">Appearance</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Dark Mode</p>
                  <p className="text-xs text-muted-foreground">Use dark theme (recommended)</p>
                </div>
                <Switch checked={true} onCheckedChange={() => {}} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Settings className="w-4 h-4 text-primary" />
                <CardTitle className="text-base">General Preferences</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-sm mb-1.5 block">Timezone</Label>
                <Input
                  defaultValue={Intl.DateTimeFormat().resolvedOptions().timeZone}
                  placeholder="e.g. America/New_York"
                  className="max-w-xs"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Integrations */}
        <TabsContent value="integrations" className="space-y-4">
          {/* Gmail */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-red-400" />
                  <div>
                    <CardTitle className="text-base">Gmail Integration</CardTitle>
                    <CardDescription>Parse emails for job updates</CardDescription>
                  </div>
                </div>
                {profile?.gmail_connected ? (
                  <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/30 flex items-center gap-1">
                    <Check className="w-3 h-3" />
                    Connected
                  </Badge>
                ) : (
                  <Badge variant="muted">Not Connected</Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {profile?.gmail_connected ? (
                <Button variant="outline" size="sm" className="text-destructive hover:text-destructive">
                  Disconnect Gmail
                </Button>
              ) : (
                <Button
                  size="sm"
                  onClick={() => window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/google`}
                >
                  Connect Gmail
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Google Calendar */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-blue-400" />
                  <div>
                    <CardTitle className="text-base">Google Calendar</CardTitle>
                    <CardDescription>Sync interview events automatically</CardDescription>
                  </div>
                </div>
                {profile?.google_calendar_connected ? (
                  <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/30 flex items-center gap-1">
                    <Check className="w-3 h-3" />
                    Connected
                  </Badge>
                ) : (
                  <Badge variant="muted">Not Connected</Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {!profile?.google_calendar_connected && (
                <Button size="sm">Connect Google Calendar</Button>
              )}
            </CardContent>
          </Card>

          {/* API Keys */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-primary" />
                <div>
                  <CardTitle className="text-base">API Keys</CardTitle>
                  <CardDescription>Configure AI providers and scrapers</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-sm mb-1.5 block">Apify API Key</Label>
                <div className="flex gap-2">
                  <Input
                    type="password"
                    value={apifyKey}
                    onChange={(e) => setApifyKey(e.target.value)}
                    placeholder="apify_api_..."
                    className="flex-1"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => updateProfile({ apify_api_key: apifyKey })}
                  >
                    Save
                  </Button>
                </div>
              </div>
              <div>
                <Label className="text-sm mb-1.5 block">OpenAI API Key</Label>
                <div className="flex gap-2">
                  <Input
                    type="password"
                    value={openaiKey}
                    onChange={(e) => setOpenaiKey(e.target.value)}
                    placeholder="sk-..."
                    className="flex-1"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => updateProfile({ openai_api_key: openaiKey })}
                  >
                    Save
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications */}
        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-primary" />
                <CardTitle className="text-base">Notification Preferences</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { label: 'New job matches', description: 'Get notified when new jobs match your profile' },
                { label: 'Application updates', description: 'Status changes in your applications' },
                { label: 'Interview reminders', description: 'Reminders 24h before interviews' },
                { label: 'Email intelligence', description: 'Important emails from recruiters parsed' },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{item.label}</p>
                    <p className="text-xs text-muted-foreground">{item.description}</p>
                  </div>
                  <Switch defaultChecked />
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Account */}
        <TabsContent value="account" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-primary" />
                <CardTitle className="text-base">Security</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-sm mb-1.5 block">New Password</Label>
                <Input type="password" placeholder="Enter new password" className="max-w-xs" />
              </div>
              <div>
                <Label className="text-sm mb-1.5 block">Confirm New Password</Label>
                <Input type="password" placeholder="Confirm password" className="max-w-xs" />
              </div>
              <Button variant="outline" size="sm">Update Password</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Data Management</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Export Your Data</p>
                  <p className="text-xs text-muted-foreground">Download all your data as JSON</p>
                </div>
                <Button variant="outline" size="sm" className="gap-2">
                  <Download className="w-4 h-4" />
                  Export
                </Button>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-destructive">Delete Account</p>
                  <p className="text-xs text-muted-foreground">Permanently delete your account and data</p>
                </div>
                <Button variant="destructive" size="sm" className="gap-2">
                  <Trash2 className="w-4 h-4" />
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
