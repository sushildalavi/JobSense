import type { ApplicationStatus } from '@jobsense/types'

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
export const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'

export const API_ROUTES = {
  // Auth
  AUTH_LOGIN: '/api/v1/auth/login',
  AUTH_REGISTER: '/api/v1/auth/register',
  AUTH_ME: '/api/v1/auth/me',
  AUTH_LOGOUT: '/api/v1/auth/logout',
  AUTH_GOOGLE: '/api/v1/auth/google',
  AUTH_REFRESH: '/api/v1/auth/refresh',

  // Jobs
  JOBS: '/api/v1/jobs',
  JOBS_SYNC: '/api/v1/jobs/sync',
  JOB_BY_ID: (id: string) => `/api/v1/jobs/${id}`,
  JOB_SHORTLIST: (id: string) => `/api/v1/jobs/${id}/shortlist`,
  JOB_MATCH: (id: string) => `/api/v1/jobs/${id}/match`,

  // Applications
  APPLICATIONS: '/api/v1/applications',
  APPLICATION_BY_ID: (id: string) => `/api/v1/applications/${id}`,
  APPLICATION_STATUS: (id: string) => `/api/v1/applications/${id}/transition`,
  APPLICATION_EVENTS: (id: string) => `/api/v1/applications/${id}/events`,

  // Resumes
  RESUMES: '/api/v1/resumes',
  RESUME_BY_ID: (id: string) => `/api/v1/resumes/${id}`,
  RESUME_UPLOAD: '/api/v1/resumes/upload',
  RESUME_VERSIONS: (id: string) => `/api/v1/resumes/${id}/versions`,
  RESUME_TAILOR: '/api/v1/resumes/tailor',

  // Profile
  PROFILE: '/api/v1/profile',

  // Analytics
  ANALYTICS: '/api/v1/analytics',
  ANALYTICS_SUMMARY: '/api/v1/analytics/summary',
  ANALYTICS_FUNNEL: '/api/v1/analytics/funnel',
  ANALYTICS_WEEKLY: '/api/v1/analytics/weekly',
  DASHBOARD_STATS: '/api/v1/analytics/dashboard',

  // Emails
  EMAIL_THREADS: '/api/v1/emails/threads',
  EMAIL_THREAD_BY_ID: (id: string) => `/api/v1/emails/threads/${id}`,
  EMAIL_SYNC: '/api/v1/emails/sync',

  // Calendar
  CALENDAR_EVENTS: '/api/v1/calendar/events',
  CALENDAR_EVENT_BY_ID: (id: string) => `/api/v1/calendar/events/${id}`,
  CALENDAR_SYNC: '/api/v1/calendar/sync',
} as const

export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  discovered: 'Discovered',
  shortlisted: 'Shortlisted',
  tailored: 'Tailored',
  ready_to_apply: 'Ready to Apply',
  applied: 'Applied',
  oa_received: 'OA Received',
  recruiter_contacted: 'Recruiter Contacted',
  interview_scheduled: 'Interview Scheduled',
  rejected: 'Rejected',
  offer: 'Offer',
  archived: 'Archived',
}

export const STATUS_COLORS: Record<ApplicationStatus, string> = {
  discovered: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
  shortlisted: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  tailored: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  ready_to_apply: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
  applied: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  oa_received: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  recruiter_contacted: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  interview_scheduled: 'bg-green-500/20 text-green-300 border-green-500/30',
  rejected: 'bg-red-500/20 text-red-300 border-red-500/30',
  offer: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  archived: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
}

export const STATUS_DOT_COLORS: Record<ApplicationStatus, string> = {
  discovered: 'bg-slate-400',
  shortlisted: 'bg-blue-400',
  tailored: 'bg-purple-400',
  ready_to_apply: 'bg-indigo-400',
  applied: 'bg-cyan-400',
  oa_received: 'bg-yellow-400',
  recruiter_contacted: 'bg-orange-400',
  interview_scheduled: 'bg-green-400',
  rejected: 'bg-red-400',
  offer: 'bg-emerald-400',
  archived: 'bg-gray-400',
}

export const QUERY_KEYS = {
  JOBS: 'jobs',
  JOB: 'job',
  APPLICATIONS: 'applications',
  APPLICATION: 'application',
  APPLICATION_EVENTS: 'application-events',
  RESUMES: 'resumes',
  RESUME: 'resume',
  RESUME_VERSIONS: 'resume-versions',
  PROFILE: 'profile',
  ANALYTICS: 'analytics',
  DASHBOARD_STATS: 'dashboard-stats',
  EMAIL_THREADS: 'email-threads',
  EMAIL_THREAD: 'email-thread',
  CALENDAR_EVENTS: 'calendar-events',
} as const

export const APPLICATION_STATUSES: ApplicationStatus[] = [
  'discovered',
  'shortlisted',
  'tailored',
  'ready_to_apply',
  'applied',
  'oa_received',
  'recruiter_contacted',
  'interview_scheduled',
  'rejected',
  'offer',
  'archived',
]

export const ACTIVE_STATUSES: ApplicationStatus[] = [
  'shortlisted',
  'tailored',
  'ready_to_apply',
  'applied',
  'oa_received',
  'recruiter_contacted',
  'interview_scheduled',
]

export const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: 'LayoutDashboard' },
  { href: '/jobs', label: 'Jobs', icon: 'Briefcase' },
  { href: '/applications', label: 'Applications', icon: 'FileText' },
  { href: '/resumes', label: 'Resumes', icon: 'FileUser' },
  { href: '/emails', label: 'Email Intelligence', icon: 'Mail' },
  { href: '/calendar', label: 'Calendar', icon: 'Calendar' },
  { href: '/analytics', label: 'Analytics', icon: 'BarChart2' },
  { href: '/settings', label: 'Settings', icon: 'Settings' },
] as const
