export type UUID = string;
export type ISODateString = string;

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface ApiError {
  detail: string;
  code?: string;
  field?: string;
}

export interface StatusResponse {
  success: boolean;
  message?: string;
}
