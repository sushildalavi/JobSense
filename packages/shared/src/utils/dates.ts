/**
 * Date utility functions for ApplyFlow.
 * All functions are browser-safe (no server-only APIs).
 */

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

export function parseISOSafe(dateStr: string): Date | null {
  if (!dateStr) return null;
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? null : d;
}

/**
 * "Jan 15, 2024"
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === "string" ? parseISOSafe(date) : date;
  if (!d) return "—";
  return `${MONTHS[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`;
}

/**
 * "Jan 15, 2024 at 2:30 PM"
 */
export function formatDateTime(date: string | Date): string {
  const d = typeof date === "string" ? parseISOSafe(date) : date;
  if (!d) return "—";
  const base = formatDate(d);
  const hours = d.getHours();
  const minutes = d.getMinutes().toString().padStart(2, "0");
  const period = hours >= 12 ? "PM" : "AM";
  const h12 = hours % 12 === 0 ? 12 : hours % 12;
  return `${base} at ${h12}:${minutes} ${period}`;
}

/**
 * "2 days ago", "in 3 hours", "just now"
 */
export function formatRelative(date: string | Date): string {
  const d = typeof date === "string" ? parseISOSafe(date) : date;
  if (!d) return "—";

  const now = Date.now();
  const diff = now - d.getTime(); // positive = past, negative = future
  const abs = Math.abs(diff);

  const seconds = Math.floor(abs / 1000);
  const minutes = Math.floor(abs / 60_000);
  const hours = Math.floor(abs / 3_600_000);
  const days = Math.floor(abs / 86_400_000);
  const weeks = Math.floor(days / 7);
  const months = Math.floor(days / 30);
  const years = Math.floor(days / 365);

  const past = diff >= 0;

  function ago(n: number, unit: string) {
    return past ? `${n} ${unit}${n !== 1 ? "s" : ""} ago` : `in ${n} ${unit}${n !== 1 ? "s" : ""}`;
  }

  if (seconds < 10) return "just now";
  if (seconds < 60) return ago(seconds, "second");
  if (minutes < 60) return ago(minutes, "minute");
  if (hours < 24) return ago(hours, "hour");
  if (days < 7) return ago(days, "day");
  if (weeks < 5) return ago(weeks, "week");
  if (months < 12) return ago(months, "month");
  return ago(years, "year");
}

/**
 * "Jan 15 – Feb 20, 2024" or "Jan 15, 2024 – Feb 20, 2025"
 */
export function formatDateRange(start: string, end: string): string {
  const s = parseISOSafe(start);
  const e = parseISOSafe(end);
  if (!s) return "—";
  if (!e) return formatDate(s) + " – Present";

  if (s.getFullYear() === e.getFullYear()) {
    return `${MONTHS[s.getMonth()]} ${s.getDate()} – ${MONTHS[e.getMonth()]} ${e.getDate()}, ${e.getFullYear()}`;
  }
  return `${formatDate(s)} – ${formatDate(e)}`;
}

export function isToday(date: string | Date): boolean {
  const d = typeof date === "string" ? parseISOSafe(date) : date;
  if (!d) return false;
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

export function isFuture(date: string | Date): boolean {
  const d = typeof date === "string" ? parseISOSafe(date) : date;
  if (!d) return false;
  return d.getTime() > Date.now();
}

export function addDays(date: Date, days: number): Date {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}
