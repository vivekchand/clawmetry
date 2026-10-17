# Jumper in ClawMetry

Jumper observation ships in the main open-source ClawMetry package. Install and
open the ordinary dashboard:

```sh
pip install clawmetry
clawmetry
```

Choose **Physical AI** to open the installed robot workbench when available.
Use its **Hardware** menu to choose Jumper on workbench versions that support
it. The built-in recorded history is also available at
`/physical-ai?hardware=jumper` on your ClawMetry server, including installations
without Pro. Its Hardware menu filters the loaded history; older matching runs
can be opened with **Load older runs**.

Both views use the existing dark dashboard style. The daemon automatically
discovers the shared local robotics journal. No separate Jumper observer plugin
or Pro license is needed for built-in observation and recorded history.

## Connect a robot application

ClawMetry can only observe telemetry a robot application exposes. The built-in
bridge attaches to an application's observation callback. It does not connect to
motor topics, install a robot SDK or start a motion controller.

```python
from clawmetry.physical_ai import JumperObserver

with JumperObserver("my-jumper", environment="hardware") as observer:
    # Call this from the application's existing telemetry callback:
    observer.observe({
        "joint_positions_rad": {"left_gripper_joint": 0.1},
        "joint_velocities_rad_s": {"left_gripper_joint": 0.0},
    })
```

Supply actual joint names from the application's robot layout, positions in
radians, velocities in radians/second and `joint_torques_nm` in newton metres
when measured. The example name above is illustrative, not a universal wire
index. Missing measurements stay unavailable. A hardware IMU alone does not
establish table coordinates, robot footprint or whether someone removed it.

The official controller has separate policy and DDS joint orders. Its motor
state and IMU topics are on-board interfaces with versioned IDL and QoS, not a
universal network discovery protocol. Direct hardware DDS connection and motor
control are not qualified by this adapter. See the pinned upstream
[wire interface](https://github.com/KingKongRobotics/jumper/tree/78966f45de6f2b6de3f7cea017f32a39f8b993e6/deploy/dds)
before writing a hardware bridge.

An application that already exports named SI-unit JSONL may instead pipe it to:

```sh
your-telemetry-exporter | clawmetry jumper observe --robot-id my-jumper --environment hardware
clawmetry jumper status
```

For an existing file, use `clawmetry jumper import-recording frames.jsonl
--robot-id my-jumper --environment hardware`. Imports are labelled recorded
evidence. This accepts the named bridge schema above, not arbitrary binary DDS
or official app bundles. Each row is bounded to 64 KiB; each import to 100,000
frames; journal disk/queue bounds and dropped evidence are visible in status.

## Observe and govern a simulation

Physics, policies and robot execution stay in the simulator host. ClawMetry's
adapter has no MuJoCo, ONNX, NumPy or simulator dependencies. Mizu's separate
scene/skills/demo project uses this built-in API.

```python
from clawmetry.physical_ai import (
    DeskMonitor, JumperObserver, Request, Task, TaskGate,
)

task = Task("desk-greeting", frozenset({"wave"}))
gate = TaskGate(task, supported_actions={"wave"}, controls_enabled=True)

with JumperObserver("mizu", environment="simulation",
                    monitor=DeskMonitor()) as observer:
    state = observer.observe(simulator.snapshot())
    decision = observer.decide(
        gate, Request("greeting-1", task.task_id, "wave"),
        state, now_s=state["time_s"],
    )
    if decision.send_to_controller:
        receipt = simulator.request_wave()
        observer.emit("controller.receipt", {"request_id": "greeting-1",
                                             "receipt": receipt})
```

Here `simulator` denotes the host's existing simulator API; these method names
are illustrative. Only list skills that host has actually qualified. The
generic gate defaults to **no qualified skills** and observation only.
`controls_enabled=True` permits the application to forward an allowed simulator
request; ClawMetry itself never invokes the controller. Hardware requests remain
unavailable even if a caller reuses an enabled simulator gate.

Desk monitoring requires fresh `time_s`, `finite: true`, measured `position_m`,
`tilt_deg`, `collision_aabb_m` and `table_bounds_m` with three-coordinate `min`
and `max` values, and a matching `table_margin_m`. The default tabletop is
1.72 by 1.16 metres and the default edge margin is 12 cm. Supply your actual
workspace in `Task.bounds_xy`; a different measured table does not authorize
the task. The gate recomputes full-body clearance and rejects stale, nonfinite,
duplicate, out-of-task or unimplemented requests. Destination checks alone do
not qualify a movement path or manipulation skill.

Call `observer.check(now_s)` from the host's heartbeat, including during missing
telemetry, using the same source clock. DeskMonitor produces one finding per
boundary, tilt, rise or missing-observation episode. An unexpected rise is a
measurement requiring review, not proof of theft or malicious intent. A
controller acknowledgement, pause or damping mode never proves a physical stop.
Simulation evidence remains labelled simulation.

## History, notifications and privacy

The existing sync daemon ingests the bounded journal into its own DuckDB store;
the dashboard reads through the normal read-only query proxy. Journals and
history stay local. Optional existing cloud sync carries the Physical AI
snapshot inside its end-to-end encrypted envelope.

Typed findings use ClawMetry's existing notification preferences and delivery
receipts. Configure a supported channel under Alerts to receive them. Fixed
incident descriptions can leave the node through that channel; raw joint state,
task content and recorded source messages are not included. A configured
channel or accepted webhook does not prove a phone displayed an alert.

Asimov and Jumper share the same evidence pipeline. Other supported robot
adapters can reuse it without creating another dashboard, database or installer.
