type LogLevel = "debug" | "info" | "warn" | "error";

const isDev =
  typeof process !== "undefined"
    ? process.env.NODE_ENV !== "production"
    : true;

function formatMessage(level: LogLevel, msg: string): string {
  const ts = new Date().toISOString();
  return `[${ts}] [${level.toUpperCase()}] ${msg}`;
}

export const logger = {
  debug: (msg: string, data?: Record<string, unknown>): void => {
    if (!isDev) return;
    console.warn(formatMessage("debug", msg), data ?? "");
  },

  info: (msg: string, data?: Record<string, unknown>): void => {
    if (!isDev) return;
    console.warn(formatMessage("info", msg), data ?? "");
  },

  warn: (msg: string, data?: Record<string, unknown>): void => {
    console.warn(formatMessage("warn", msg), data ?? "");
  },

  error: (
    msg: string,
    error?: Error,
    data?: Record<string, unknown>
  ): void => {
    console.error(formatMessage("error", msg), error ?? "", data ?? "");
  },
};
