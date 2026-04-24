import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { createClawMetryService } from "./src/service.js";

export default definePluginEntry({
  id: "clawmetry",
  name: "ClawMetry",
  description: "Real-time observability dashboard for OpenClaw agents",
  register(api) {
    api.registerService(createClawMetryService());
  },
});
