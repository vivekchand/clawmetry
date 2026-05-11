const DASHBOARD_HEALTH_PATH = "/api/health";
const EVENT_BUFFER_FLUSH_MS = 2000;
const EVENT_BUFFER_MAX_SIZE = 100;
const DASHBOARD_EVENT_PATH = "/api/plugin/events";
/**
 * Creates the ClawMetry plugin service that:
 * 1. Subscribes to OpenClaw plugin hooks (tool calls, LLM usage, sessions)
 * 2. Buffers structured telemetry events
 * 3. Forwards them to the ClawMetry dashboard via HTTP
 *
 * The dashboard itself is managed separately (systemd/launchd/manual).
 * This plugin only forwards telemetry — no subprocess spawning.
 */
export function createClawMetryService(api, config) {
    let eventBuffer = [];
    let flushTimer = null;
    let dashboardAvailable = false;
    function getDashboardUrl() {
        const host = config.host ?? "127.0.0.1";
        const port = config.port ?? 8900;
        return `http://${host}:${port}`;
    }
    async function checkDashboard() {
        try {
            const url = `${getDashboardUrl()}${DASHBOARD_HEALTH_PATH}`;
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 3000);
            const response = await fetch(url, { signal: controller.signal });
            clearTimeout(timeout);
            return response.ok;
        }
        catch {
            return false;
        }
    }
    function bufferEvent(type, payload) {
        eventBuffer.push({
            type,
            timestamp: new Date().toISOString(),
            payload,
        });
        if (eventBuffer.length >= EVENT_BUFFER_MAX_SIZE) {
            void flushEvents();
        }
    }
    async function flushEvents() {
        if (eventBuffer.length === 0)
            return;
        if (!dashboardAvailable) {
            dashboardAvailable = await checkDashboard();
            if (!dashboardAvailable)
                return;
        }
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
        }
        catch {
            dashboardAvailable = false;
            if (eventBuffer.length < EVENT_BUFFER_MAX_SIZE * 2) {
                eventBuffer.unshift(...batch);
            }
        }
    }
    function registerHooks() {
        api.on("after_tool_call", (event) => {
            const e = event;
            bufferEvent("tool.call", {
                toolName: e.toolName,
                durationMs: e.durationMs,
                error: e.error ? String(e.error) : undefined,
                sessionId: e.context?.sessionId,
                sessionKey: e.context?.sessionKey,
            });
        });
        api.on("llm_output", (event) => {
            const e = event;
            const usage = e.usage;
            bufferEvent("model.usage", {
                provider: e.provider,
                model: e.model,
                inputTokens: usage?.inputTokens,
                outputTokens: usage?.outputTokens,
                cacheReadTokens: usage?.cacheReadTokens,
                cacheWriteTokens: usage?.cacheWriteTokens,
                costUsd: usage?.costUsd,
                durationMs: e.durationMs,
                sessionId: e.sessionId,
                sessionKey: e.sessionKey,
            });
        });
        api.on("session_start", (event) => {
            const e = event;
            bufferEvent("session.start", {
                sessionId: e.sessionId,
                sessionKey: e.sessionKey,
                channel: e.channel,
            });
        });
        api.on("session_end", (event) => {
            const e = event;
            bufferEvent("session.end", {
                sessionId: e.sessionId,
                sessionKey: e.sessionKey,
                reason: e.reason,
            });
        });
        api.on("message_received", (event) => {
            const e = event;
            bufferEvent("message.received", {
                sessionId: e.sessionId,
                channel: e.channel,
            });
        });
        api.on("message_sent", (event) => {
            const e = event;
            bufferEvent("message.sent", {
                sessionId: e.sessionId,
                channel: e.channel,
                success: e.success,
            });
        });
    }
    return {
        id: "clawmetry",
        registerHooks,
        async start(_ctx) {
            dashboardAvailable = await checkDashboard();
            if (dashboardAvailable) {
                console.log(`[clawmetry] Dashboard detected at ${getDashboardUrl()}`);
            }
            else {
                console.log(`[clawmetry] Dashboard not detected at ${getDashboardUrl()}. ` +
                    `Start it with: clawmetry --port ${config.port ?? 8900}`);
            }
            flushTimer = setInterval(() => void flushEvents(), EVENT_BUFFER_FLUSH_MS);
            console.log("[clawmetry] Plugin started — telemetry forwarding active");
        },
        async stop(_ctx) {
            await flushEvents();
            if (flushTimer) {
                clearInterval(flushTimer);
                flushTimer = null;
            }
            console.log("[clawmetry] Plugin stopped");
        },
    };
}
//# sourceMappingURL=service.js.map