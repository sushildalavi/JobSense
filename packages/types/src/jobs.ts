import type { UUID, ISODateString } from "./common";
import type { SeniorityLevel } from "./profile";

export type EmploymentType =
  | "full_time"
  | "part_time"
  | "contract"
  | "internship"
  | "freelance";

export type JobStatus = "active" | "expired" | "removed";

export interface Job {
  id: UUID;
  source_id: UUID;
  source_job_id: string;
  company_name: string;
  company_website?: string;
  title: string;
  location: string;
  is_remote: boolean;
  is_hybrid: boolean;
  is_onsite: boolean;
  employment_type: EmploymentType;
  seniority: SeniorityLevel;
  salary_text?: string;
  salary_min?: number;
  salary_max?: number;
  currency?: string;
  cleaned_description: string;
  requirements: string[];
  preferred_qualifications: string[];
  responsibilities: string[];
  apply_url: string;
  posting_date?: ISODateString;
  ingestion_timestamp: ISODateString;
  status: JobStatus;
  match?: JobMatch;
  created_at: ISODateString;
}

export interface JobListItem {
  id: UUID;
  company_name: string;
  title: string;
  location: string;
  is_remote: boolean;
  employment_type: EmploymentType;
  seniority: SeniorityLevel;
  salary_text?: string;
  apply_url: string;
  posting_date?: ISODateString;
  match_score?: number;
  created_at: ISODateString;
}

export interface JobMatch {
  id: UUID;
  job_id: UUID;
  user_id: UUID;
  match_score: number;
  skill_matches: string[];
  skill_gaps: string[];
  strengths: string[];
  weaknesses: string[];
  explanation: string;
  computed_at: ISODateString;
}

export interface JobSource {
  id: UUID;
  name: string;
  connector_type: string;
  is_active: boolean;
  last_synced_at?: ISODateString;
}

export interface JobFilter {
  source?: string;
  location?: string;
  is_remote?: boolean;
  employment_type?: EmploymentType;
  seniority?: SeniorityLevel;
  min_match_score?: number;
  search?: string;
  skip?: number;
  limit?: number;
}
