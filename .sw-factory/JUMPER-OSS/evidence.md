# Verified source evidence

Actual official Jumper native35-second replay through the built-in main package, with an unmodified pinned upstream and official imported tabletop scene. The host supplies22 named measured hinge positions/velocities; torque is unavailable. No reset or per-frame pose teleport.

- Shared run: `535dbf83af5849969f3e3d34d266d72d`
- 7,000 control steps, all finite, zero resets; measured minimum full-body margin0.3102791896m; maximum tilt10.253523883degrees.
- All366 events arrived:351 observations,3 requests,3 taskdecisions,6 nativecontrollerreceipts,1 declined-task incident, start/end. Zero journal drops/errors, fully flushed.
- Actual daemon journal worker in a separate process discovered the source, persisted the complete run to its owned scratch DuckDB. Dashboard was forced into normal `_ProxyStore` and read via authenticated localhost RPC; no handler file reads or second writer.
- Actual desktop and390px browser rendered22 joints, clearance, decisions and receipts with zero JavaScript errors and no horizontal overflow. Local screenshot/report paths are in context.md, no raw user data or credentials are committed.
- Generic snapshot11,474bytes includes bounded traces; legacy Asimov APIs stay filtered. Native incident delivery disabled via isolated preferences for this replay; shared preference, receipt and cooldown behavior has separate focused integration tests. No phone-delivery claim.
- Clean candidate wheel installs into freshvenv with no clawmetry_pro, MuJoCo, NumPy or ONNXRuntime; observer imported and wrote/flushed a named hardware-frame journal. Wheel contains physical_ai package, routes and static/template assets. Candidateversion is not a publishedrelease claim.

Independentreviews: root/observer/UI approved by cloud_guard_review; store/query/snapshot/alerts approved round2 by runtime_gate_diagnosis after strictcursor fix. Current sourcefiles are complete; public release/cloud/live verification remains pending and will be recorded separately.
