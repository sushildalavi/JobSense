import type { UUID, ISODateString } from "./common";

export type CalendarEventStatus = "pending" | "confirmed" | "cancelled";

export interface CalendarEvent {
  id: UUID;
  application_id?: UUID;
  parsed_email_id?: UUID;
  google_event_id?: string;
  title: string;
  description?: string;
  start_datetime: ISODateString;
  end_datetime: ISODateString;
  timezone: string;
  meeting_link?: string;
  location?: string;
  status: CalendarEventStatus;
  reminder_minutes: number[];
  created_at: ISODateString;
}
