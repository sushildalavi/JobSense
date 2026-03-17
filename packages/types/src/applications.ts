import type { UUID, ISODateString } from "./common";
import type { JobListItem } from "./jobs";

export type ApplicationStatus =
  | "discovered"
  | "shortlisted"
  | "tailored"
  | "ready_to_apply"
  | "applied"
  | "oa_received"
  | "recruiter_contacted"
  | "interview_scheduled"
  | "rejected"
  | "offer"
  | "archived";

export type EventTrigger = "user" | "email_parser" | "agent" | "automation";

export interface Application {
  id: UUID;
  user_id: UUID;
  job_id: UUID;
  job?: JobListItem;
  resume_version_id?: UUID;
  status: ApplicationStatus;
  applied_at?: ISODateString;
  notes?: string;
  custom_answers?: Record<string, string>;
  cover_letter?: string;
  application_url?: string;
  source_of_discovery?: string;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export interface ApplicationEvent {
  id: UUID;
  application_id: UUID;
  from_status?: ApplicationStatus;
  to_status: ApplicationStatus;
  triggered_by: EventTrigger;
  notes?: string;
  created_at: ISODateString;
}

export interface ApplicationListItem {
  id: UUID;
  job_id: UUID;
  company_name: string;
  job_title: string;
  location: string;
  status: ApplicationStatus;
  applied_at?: ISODateString;
  created_at: ISODateString;
}
