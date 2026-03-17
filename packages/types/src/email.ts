import type { UUID, ISODateString } from "./common";

export type EmailClassification =
  | "recruiter_outreach"
  | "oa_assessment"
  | "interview_scheduling"
  | "interview_confirmation"
  | "rejection"
  | "offer"
  | "follow_up"
  | "noise"
  | "unclassified";

export interface EmailThread {
  id: UUID;
  thread_id: string;
  subject: string;
  participants: string[];
  last_message_at: ISODateString;
  message_count: number;
  classification: EmailClassification;
  confidence_score: number;
  application_id?: UUID;
  parsed_emails?: ParsedEmail[];
  created_at: ISODateString;
}

export interface ParsedEmail {
  id: UUID;
  message_id: string;
  subject: string;
  sender_email: string;
  sender_name?: string;
  received_at: ISODateString;
  classification: EmailClassification;
  confidence_score: number;
  extracted_company?: string;
  extracted_job_title?: string;
  extracted_interviewer_name?: string;
  extracted_interview_datetime?: ISODateString;
  extracted_timezone?: string;
  extracted_meeting_link?: string;
  extracted_next_action?: string;
  extracted_data: Record<string, unknown>;
}
