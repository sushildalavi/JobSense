import type { UUID, ISODateString } from "./common";

export interface MasterResume {
  id: UUID;
  user_id: UUID;
  name: string;
  raw_text: string;
  parsed_data: ParsedResumeData;
  file_url?: string;
  file_name?: string;
  is_active: boolean;
  created_at: ISODateString;
}

export interface ParsedResumeData {
  summary?: string;
  experience: WorkExperience[];
  education: Education[];
  skills: string[];
  projects: Project[];
  certifications?: string[];
  publications?: string[];
  achievements?: string[];
}

export interface WorkExperience {
  company: string;
  title: string;
  start_date: string;
  end_date?: string;
  is_current: boolean;
  location?: string;
  description: string;
  achievements: string[];
  technologies: string[];
}

export interface Education {
  institution: string;
  degree: string;
  field: string;
  start_date: string;
  end_date?: string;
  gpa?: number;
}

export interface Project {
  name: string;
  description: string;
  technologies: string[];
  url?: string;
}

export interface ResumeVersion {
  id: UUID;
  master_resume_id: UUID;
  job_id?: UUID;
  application_id?: UUID;
  name: string;
  tailored_content: string;
  tailoring_strategy: TailoringStrategy;
  pdf_url?: string;
  ai_model_used?: string;
  created_at: ISODateString;
}

export interface TailoringStrategy {
  sections_modified: string[];
  keywords_added: string[];
  skills_emphasized: string[];
  experience_reframed: string[];
  reasoning: string;
}

export interface TailoringRequest {
  job_id: UUID;
  master_resume_id: UUID;
  additional_instructions?: string;
}
