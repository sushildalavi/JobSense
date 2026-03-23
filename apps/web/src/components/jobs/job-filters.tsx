'use client'

import { useState } from 'react'
import { Search, X, SlidersHorizontal } from 'lucide-react'
import type { JobFilter, EmploymentType, SeniorityLevel } from '@jobsense/types'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'

interface JobFiltersProps {
  filters: JobFilter
  onChange: (filters: JobFilter) => void
}

const remoteOptions = [
  { label: 'Remote', key: 'is_remote' as const, color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' },
]

const seniorityOptions: SeniorityLevel[] = [
  'intern', 'entry', 'junior', 'mid', 'senior', 'staff', 'lead', 'manager',
]

const employmentTypes: EmploymentType[] = [
  'full_time', 'part_time', 'contract', 'internship', 'freelance',
]

const scoreOptions = [0, 40, 60, 70, 80]

export function JobFilters({ filters, onChange }: JobFiltersProps) {
  const [searchValue, setSearchValue] = useState(filters.search || '')

  const handleSearchSubmit = () => {
    onChange({ ...filters, search: searchValue || undefined })
  }

  const handleRemoteToggle = () => {
    onChange({ ...filters, is_remote: filters.is_remote ? undefined : true })
  }

  const clearAll = () => {
    setSearchValue('')
    onChange({ limit: filters.limit, skip: 0 })
  }

  const hasFilters =
    filters.search ||
    filters.is_remote ||
    filters.employment_type ||
    filters.seniority ||
    filters.min_match_score

  return (
    <div className="space-y-5 p-4 rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">Filters</span>
        </div>
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clearAll} className="text-xs h-7">
            <X className="w-3 h-3 mr-1" />
            Clear all
          </Button>
        )}
      </div>

      {/* Search */}
      <div>
        <Label className="text-xs text-muted-foreground mb-2 block">Search</Label>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
            <Input
              placeholder="Search jobs..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearchSubmit()}
              className="pl-9 h-9 text-sm"
            />
          </div>
          <Button size="sm" onClick={handleSearchSubmit} className="h-9">
            Go
          </Button>
        </div>
      </div>

      {/* Work type */}
      <div>
        <Label className="text-xs text-muted-foreground mb-2 block">Work Type</Label>
        <div className="flex flex-wrap gap-2">
          {remoteOptions.map((opt) => (
            <button
              key={opt.key}
              onClick={() => handleRemoteToggle()}
              className={cn(
                'px-3 py-1 rounded-full text-xs font-medium border transition-all',
                filters[opt.key]
                  ? opt.color
                  : 'border-border text-muted-foreground hover:border-primary/50'
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Employment type */}
      <div>
        <Label className="text-xs text-muted-foreground mb-2 block">Employment Type</Label>
        <Select
          value={filters.employment_type || 'all'}
          onValueChange={(v) =>
            onChange({ ...filters, employment_type: v === 'all' ? undefined : (v as EmploymentType) })
          }
        >
          <SelectTrigger className="h-9 text-sm">
            <SelectValue placeholder="All types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            {employmentTypes.map((t) => (
              <SelectItem key={t} value={t}>
                {t.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Seniority */}
      <div>
        <Label className="text-xs text-muted-foreground mb-2 block">Seniority</Label>
        <Select
          value={filters.seniority || 'all'}
          onValueChange={(v) =>
            onChange({ ...filters, seniority: v === 'all' ? undefined : (v as SeniorityLevel) })
          }
        >
          <SelectTrigger className="h-9 text-sm">
            <SelectValue placeholder="All levels" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All levels</SelectItem>
            {seniorityOptions.map((s) => (
              <SelectItem key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Min match score */}
      <div>
        <Label className="text-xs text-muted-foreground mb-2 block">
          Min Match Score {filters.min_match_score ? `(${filters.min_match_score}%+)` : ''}
        </Label>
        <div className="flex flex-wrap gap-1.5">
          {scoreOptions.map((score) => (
            <button
              key={score}
              onClick={() =>
                onChange({
                  ...filters,
                  min_match_score: filters.min_match_score === score ? undefined : score,
                })
              }
              className={cn(
                'px-2.5 py-1 rounded-full text-xs font-medium border transition-all',
                filters.min_match_score === score
                  ? 'bg-primary/20 text-primary border-primary/30'
                  : 'border-border text-muted-foreground hover:border-primary/50'
              )}
            >
              {score === 0 ? 'Any' : `${score}%+`}
            </button>
          ))}
        </div>
      </div>

      {/* Active filters summary */}
      {hasFilters && (
        <div className="pt-2 border-t border-border">
          <p className="text-xs text-muted-foreground mb-2">Active filters:</p>
          <div className="flex flex-wrap gap-1.5">
            {filters.search && (
              <Badge variant="outline" className="text-xs gap-1">
                Search: {filters.search}
                <X
                  className="w-3 h-3 cursor-pointer"
                  onClick={() => { setSearchValue(''); onChange({ ...filters, search: undefined }) }}
                />
              </Badge>
            )}
            {filters.is_remote && (
              <Badge variant="outline" className="text-xs gap-1">
                Remote
                <X className="w-3 h-3 cursor-pointer" onClick={() => onChange({ ...filters, is_remote: undefined })} />
              </Badge>
            )}
            {filters.min_match_score && (
              <Badge variant="outline" className="text-xs gap-1">
                {filters.min_match_score}%+ match
                <X className="w-3 h-3 cursor-pointer" onClick={() => onChange({ ...filters, min_match_score: undefined })} />
              </Badge>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
