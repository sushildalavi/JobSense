import type { UUID, ISODateString } from "./common";

export type WorkflowName =
  | "job_discovery"
  | "job_matching"
  | "resume_tailoring"
  | "email_classification"
  | "email_extraction"
  | "calendar_automation"
  | "follow_up_draft";

export type AgentRunStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface AgentRun {
  id: UUID;
  user_id?: UUID;
  workflow_name: WorkflowName;
  status: AgentRunStatus;
  input_data: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  error_message?: string;
  tokens_used?: number;
  duration_ms?: number;
  started_at?: ISODateString;
  completed_at?: ISODateString;
  created_at: ISODateString;
}
