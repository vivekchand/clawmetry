import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
interface PluginServiceContext {
    config?: Record<string, unknown>;
}
interface PluginService {
    id: string;
    start: (ctx: PluginServiceContext) => void | Promise<void>;
    stop?: (ctx: PluginServiceContext) => void | Promise<void>;
}
interface ClawMetryConfig {
    port?: number;
    host?: string;
    autoStart?: boolean;
    cloudSync?: boolean;
    apiKey?: string;
}
/**
 * Creates the ClawMetry plugin service that:
 * 1. Subscribes to OpenClaw plugin hooks (tool calls, LLM usage, sessions)
 * 2. Buffers structured telemetry events
 * 3. Forwards them to the ClawMetry dashboard via HTTP
 *
 * The dashboard itself is managed separately (systemd/launchd/manual).
 * This plugin only forwards telemetry — no subprocess spawning.
 */
export declare function createClawMetryService(api: OpenClawPluginApi, config: ClawMetryConfig): PluginService & {
    registerHooks(): void;
};
export {};
//# sourceMappingURL=service.d.ts.map