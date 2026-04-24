import { createClawMetryService } from "./src/service.js";
const plugin = {
    id: "clawmetry",
    name: "ClawMetry",
    description: "Real-time observability for OpenClaw agents — local dashboard + E2E encrypted cloud sync",
    register(api) {
        const config = (api.pluginConfig ?? {});
        const service = createClawMetryService(api, config);
        service.registerHooks();
        api.registerService(service);
    },
};
export default plugin;
//# sourceMappingURL=index.js.map