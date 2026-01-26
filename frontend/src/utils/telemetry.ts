type TelemetryPayload = Record<string, unknown>

export function trackEvent(name: string, payload: TelemetryPayload = {}) {
  if (import.meta.env.DEV) {
    console.info('[telemetry]', name, payload)
  }
  // TODO: Hook into real analytics provider (PostHog/GA/Sentry)
}
