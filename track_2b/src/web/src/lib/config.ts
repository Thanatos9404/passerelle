export type DataSource = "mock" | "api";

const envSource = process.env.NEXT_PUBLIC_DATA_SOURCE;

/**
 * Data source selection:
 *  - NEXT_PUBLIC_DATA_SOURCE=mock|api wins;
 *  - otherwise `next dev` uses the mock and production builds use the API;
 *  - a `?data=mock` / `?data=api` URL parameter overrides at runtime (handy for demos).
 */
export function resolveDataSource(): DataSource {
  if (typeof window !== "undefined") {
    const q = new URLSearchParams(window.location.search).get("data");
    if (q === "mock" || q === "api") return q;
  }
  if (envSource === "mock" || envSource === "api") return envSource;
  return process.env.NODE_ENV === "development" ? "mock" : "api";
}

/** Empty string = same origin (FastAPI serves the static export and /api/*). */
export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE ?? "").replace(/\/$/, "");
