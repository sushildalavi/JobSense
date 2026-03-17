import type { ApplicationStatus } from "./applications";

export interface DashboardStats {
  total_jobs_discovered: number;
  total_shortlisted: number;
  total_applied: number;
  total_interviews: number;
  total_offers: number;
  total_rejections: number;
  active_applications: number;
  response_rate: number;
  interview_rate: number;
  offer_rate: number;
}

export interface FunnelStage {
  status: ApplicationStatus;
  count: number;
  percentage: number;
}

export interface SourceStat {
  source: string;
  count: number;
}

export interface WeeklyStat {
  week: string;
  applications: number;
  interviews: number;
}

export interface ScoreBucket {
  range: string;
  count: number;
}

export interface AnalyticsSummary {
  stats: DashboardStats;
  funnel: FunnelStage[];
  by_source: SourceStat[];
  weekly_activity: WeeklyStat[];
  match_score_distribution: ScoreBucket[];
}
