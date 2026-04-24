import type { OpenClawPluginService } from "openclaw/plugin-sdk/plugin-entry";
import { onDiagnosticEvent, registerLogTransport } from "openclaw/plugin-sdk/diagnostics-otel";
import { spawn, type ChildProcess } from "child_process";
import { homedir } from "os";
import { existsSync } from "fs";
import { join } from "path";

const DASHBOARD_HEALTH_PATH = "/api/health";
const EVENT_BUFFER_FLUSH_MS = 2000;
const EVENT_BUFFER_MAX_SIZE = 100;
const DASHBOARD_EVENT_PATH = "/api/plugin/events";

interface ClawMetryConfig {
  port?: number;
  host?: string;
  autoStart?: boolean;
  cloudSync?: boolean;
  apiKey?: string;
}

interface BufferedEvent {
  type: string;
  timestamp: string;
  payload: Record<string, unknown>;
}

/**
 * Creates the ClawMetry background service that:
 * 1. Manages the ClawMetry dashboard process (auto-start/stop)
 * 2. Subscribes to OpenClaw diagnostic events
 * 3. Forwards structured telemetry to the dashboard via HTTP
 */
export function createClawMetryService(): OpenClawPluginService {
  let dashboardProcess: ChildProcess | null = null;
  let config: ClawMetryConfig = {};
  let eventBuffer: BufferedEvent[] = [];
  let flushTimer: ReturnType<typeof setInterval> | null = null;
  let stopped = false;

  function getDashboardUrl(): string {
    const host = config.host ?? "127.0.0.1";
    const port = config.port ?? 8900;
    return `http://${host}:${port}`;
  }

  function findClawMetryBinary(): string | null {
    // Check common locations
    const candidates = [
      join(homedir(), ".local", "bin", "clawmetry"),
      "/usr/local/bin/clawmetry",
      "/usr/bin/clawmetry",
    ];
    for (const candidate of candidates) {
      if (existsSync(candidate)) {
        return candidate;
      }
    }
    // Fallback: assume it's on PATH
    return "clawmetry";
  }

  async function isDashboardRunning(): Promise<boolean> {
    try {
      const url = `${getDashboardUrl()}${DASHBOARD_HEALTH_PATH}`;
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);
      const response = await fetch(url, { signal: controller.signal });
      clearTimeout(timeout);
      return response.ok;
    } catch {
      return false;
    }
  }

  function startDashboard(): void {
    const binary = findClawMetryBinary();
    if (!binary) {
      console.error("[clawmetry] Could not find clawmetry binary. Install with: pip install clawmetry");
      return;
    }

    const port = String(config.port ?? 8900);
    const host = config.host ?? "127.0.0.1";

    const args = ["--host", host, "--port", port];
    if (config.cloudSync && config.apiKey) {
      args.push("--cloud");
    }

    dashboardProcess = spawn(binary, args, {
      stdio: "ignore",
      detached: true,
      env: {
        ...process.env,
        CLAWMETRY_PORT: port,
        CLAWMETRY_HOST: host,
        CLAWMETRY_PLUGIN_MODE: "1",
        ...(config.apiKey ? { CLAWMETRY_API_KEY: config.apiKey } : {}),
      },
    });

    dashboardProcess.unref();

    dashboardProcess.on("error", (err) => {
      console.error(`[clawmetry] Failed to start dashboard: ${err.message}`);
      dashboardProcess = null;
    });

    dashboardProcess.on("exit", (code) => {
      if (!stopped) {
        console.warn(`[clawmetry] Dashboard exited with code ${code}`);
      }
      dashboardProcess = null;
    });

    console.log(`[clawmetry] Dashboard starting on ${host}:${port}`);
  }

  function bufferEvent(type: string, payload: Record<string, unknown>): void {
    eventBuffer.push({
      type,
      timestamp: new Date().toISOString(),
      payload,
    });

    if (eventBuffer.length >= EVENT_BUFFER_MAX_SIZE) {
      void flushEvents();
    }
  }

  async function flushEvents(): Promise<void> {
    if (eventBuffer.length === 0) return;

    const batch = eventBuffer.splice(0);
    try {
      const url = `${getDashboardUrl()}${DASHBOARD_EVENT_PATH}`;
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ events: batch }),
        signal: controller.signal,
      });
      clearTimeout(timeout);
    } catch {
      // Dashboard might not be ready yet — re-buffer events
      // Only keep recent events to avoid unbounded growth
      if (eventBuffer.length < EVENT_BUFFER_MAX_SIZE * 2) {
        eventBuffer.unshift(...batch);
      }
    }
  }

  function subscribeToDiagnostics(): void {
    // Subscribe to all diagnostic events emitted by the OpenClaw runtime
    onDiagnosticEvent((event) => {
      const { name, attributes } = event;

      switch (name) {
        case "model.usage":
          bufferEvent("model.usage", {
            provider: attributes["openclaw.provider"],
            model: attributes["openclaw.model"],
            inputTokens: attributes["openclaw.inputTokens"],
            outputTokens: attributes["openclaw.outputTokens"],
            cacheReadTokens: attributes["openclaw.cacheReadTokens"],
            cacheWriteTokens: attributes["openclaw.cacheWriteTokens"],
            costUsd: attributes["openclaw.costUsd"],
            durationMs: attributes["openclaw.durationMs"],
            sessionId: attributes["openclaw.sessionId"],
            sessionKey: attributes["openclaw.sessionKey"],
            channel: attributes["openclaw.channel"],
            api: attributes["openclaw.api"],
          });
          break;

        case "message.queued":
        case "message.processed":
          bufferEvent(name, {
            sessionId: attributes["openclaw.sessionId"],
            channel: attributes["openclaw.channel"],
            direction: attributes["openclaw.direction"],
          });
          break;

        case "session.state":
          bufferEvent("session.state", {
            sessionId: attributes["openclaw.sessionId"],
            sessionKey: attributes["openclaw.sessionKey"],
            state: attributes["openclaw.state"],
          });
          break;

        case "session.stuck":
          bufferEvent("session.stuck", {
            sessionId: attributes["openclaw.sessionId"],
            reason: attributes["openclaw.reason"],
          });
          break;

        case "run.attempt":
          bufferEvent("run.attempt", {
            sessionId: attributes["openclaw.sessionId"],
            runId: attributes["openclaw.runId"],
            attempt: attributes["openclaw.attempt"],
          });
          break;

        case "diagnostic.heartbeat":
          bufferEvent("heartbeat", {
            uptimeMs: attributes["openclaw.uptimeMs"],
            activeSessions: attributes["openclaw.activeSessions"],
          });
          break;

        case "webhook.received":
        case "webhook.processed":
        case "webhook.error":
          bufferEvent(name, {
            channel: attributes["openclaw.channel"],
            ...(attributes["openclaw.error"] ? { error: attributes["openclaw.error"] } : {}),
          });
          break;

        default:
          // Forward any unknown diagnostic events as generic telemetry
          bufferEvent(name, attributes as Record<string, unknown>);
          break;
      }
    });

    // Also capture gateway logs for the log viewer
    registerLogTransport((entry) => {
      bufferEvent("log", {
        level: entry.level,
        message: entry.message,
        ...(entry.bindings ?? {}),
      });
    });
  }

  return {
    async start(ctx) {
      config = (ctx.config ?? {}) as ClawMetryConfig;
      stopped = false;

      // Subscribe to diagnostic events immediately
      subscribeToDiagnostics();

      // Start periodic flush
      flushTimer = setInterval(() => void flushEvents(), EVENT_BUFFER_FLUSH_MS);

      // Auto-start dashboard if configured (default: true)
      if (config.autoStart !== false) {
        const alreadyRunning = await isDashboardRunning();
        if (alreadyRunning) {
          console.log(`[clawmetry] Dashboard already running at ${getDashboardUrl()}`);
        } else {
          startDashboard();
        }
      }

      console.log("[clawmetry] Plugin started — observability active");
    },

    async stop() {
      stopped = true;

      // Flush remaining events
      await flushEvents();

      // Clear flush timer
      if (flushTimer) {
        clearInterval(flushTimer);
        flushTimer = null;
      }

      // Stop dashboard if we started it
      if (dashboardProcess) {
        dashboardProcess.kill("SIGTERM");
        dashboardProcess = null;
      }

      console.log("[clawmetry] Plugin stopped");
    },
  };
}
