import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { createClawMetryService } from "./src/service.js";

interface ClawMetryConfig {
  port?: number;
  host?: string;
  autoStart?: boolean;
  cloudSync?: boolean;
  apiKey?: string;
}

const plugin = {
  id: "clawmetry",
  name: "ClawMetry",
  description: "Real-time observability for OpenClaw agents — local dashboard + E2E encrypted cloud sync",
  register(api: OpenClawPluginApi) {
    const config = (api.pluginConfig ?? {}) as ClawMetryConfig;
    const service = createClawMetryService(api, config);
    service.registerHooks();
    api.registerService(service);
  },
};

export default plugin;
