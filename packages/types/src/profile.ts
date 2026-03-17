import type { UUID, ISODateString } from "./common";

export type RemotePreference = "remote_only" | "hybrid" | "onsite" | "flexible";

export type SeniorityLevel =
  | "intern"
  | "entry"
  | "junior"
  | "mid"
  | "senior"
  | "staff"
  | "principal"
  | "lead"
  | "manager"
  | "director"
  | "vp"
  | "c_level";

export interface Profile {
  id: UUID;
  user_id: UUID;

  // Target roles and level
  target_roles: string[];
  target_seniority: SeniorityLevel[];
  years_of_experience: number;

  // Location preferences
  preferred_locations: string[];
  remote_preference: RemotePreference;

  // Industry preferences
  preferred_industries: string[];
  excluded_companies: string[];

  // Compensation expectations
  salary_min?: number;
  salary_max?: number;
  salary_currency: string;

  // Skills and keywords
  skills: string[];
  priority_keywords: string[];
  avoid_keywords: string[];

  // External links
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  personal_website?: string;

  // Integration settings
  gmail_connected: boolean;
  google_calendar_connected: boolean;
  apify_api_key?: string;
  openai_api_key?: string;
  anthropic_api_key?: string;

  // Active master resume
  active_resume_id?: UUID;

  created_at: ISODateString;
  updated_at: ISODateString;
}
