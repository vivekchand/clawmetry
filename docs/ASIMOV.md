# Asimov 1 observation

ClawMetry includes a free, open-source connector for the Menlo Asimov 1 humanoid.
It imports official SDK recordings and observes live state.
It can also record command evidence from an application that explicitly installs tracing.

Hardware qualification is pending. SDK tests and imported recordings do not establish physical robot validation.
The connector cannot confirm command acceptance, physical movement, or task success from an SDK return value.

## Inspect a recording

Recording import does not require the Menlo SDK or a paid ClawMetry license.
Use an official Menlo SDK JSONL recording.
Choose an identifier for the robot that produced it.

```sh
clawmetry asimov import-recording /path/to/run.jsonl --robot-id my-asimov
clawmetry asimov status
clawmetry
```

Open `/asimov` on your local ClawMetry dashboard.
The sync daemon imports the connector journal into DuckDB.
The web page reads persisted evidence through the daemon.
It does not read recording files or connect to the robot.

Use the run ID from `status` to inspect its journal from the command line.

```sh
clawmetry asimov inspect RUN_ID
```

An imported recording always appears as recorded evidence.
Its recent import time does not make it a live robot connection.
Repeated imports with the same file, robot identifier, environment, and source label reuse the same run identity.
Malformed rows are skipped where possible. Recorder status reports incomplete evidence.

## Observe live state

Live observation requires Python 3.12 or later and Menlo SDK 0.1.0.
These dependencies are optional. Ordinary ClawMetry use does not load them.
Use a Python environment that contains both packages.

```sh
python -m pip install clawmetry 'menlo-sdk==0.1.0'
clawmetry asimov observe --help
clawmetry asimov observe --robot-id my-asimov --duration 60
```

Use an Observe credential from Asimov Manager.
Set `MENLO_MANAGER_URL` and `MENLO_CREDENTIAL` together.
You can also use an Observe connection saved by `menlo setup`.
Keep the credential outside source code and shell history.
Use `--manager-url` with an explicit environment credential for a separate manager.
The collector does not send a saved credential to a different manager.
The collector uses a data-only connection. It does not subscribe to camera or audio tracks.

An Observe credential cannot grant robot control.
The collector rejects control authority and calls no motion or mode command.
Closing observation does not stop the robot or take ownership from its application.

## Trace an application

Install tracing explicitly around the application code that already controls the robot.
The application retains connection and motion ownership.

```python
from clawmetry.asimov import observe

# robot is an existing, connected Menlo SDK Robot instance.
with observe(robot, robot_id="my-asimov"):
    run_existing_application(robot)
```

Tracing records requests, returns, and exceptions from supported synchronous SDK commands.
It preserves the original return value or exception.
A command request records intent. A returned call records an application result.
Neither establishes that the robot accepted a command or completed a movement.
Command outcomes remain unknown without authoritative physical evidence.
ClawMetry does not patch an SDK application unless it explicitly installs tracing.

## Read the evidence

The page separates robot runs by source and environment.
It shows the latest persisted mode, observation age, battery, alerts, and joint measurements.
Available measurements use radians, radians per second, amps, and degrees Celsius.
Quaternion orientation uses w, x, y, z order.
Missing measurements appear as `Not reported`. They do not become zero.

Source clocks come from robot firmware or a recording.
Receipt clocks come from the collector computer.
The connector preserves these clocks separately and does not infer a shared clock.
The event sequence orders stored evidence.

The command evidence list reads the selected run in bounded pages.
It does not infer a task outcome or reconstruct agent reasoning.
A separate observation connection cannot see commands issued by an uninstrumented application.

The page polls while visible. It stops polling when the browser tab is hidden.
Imported recordings never receive a live status.
Lost telemetry, stale state, dropped evidence, and incomplete recordings remain visible.
If the daemon is unavailable, the page explains that stored values may be old.

## Storage and cloud

The producer uses a bounded queue and writes compatible `clawmetry.robotics.v1` journals.
The daemon owns the DuckDB writer. Web handlers request read-only store queries.
Queue or disk limits can drop evidence. Check `clawmetry asimov status` before treating a run as complete.
Use `--journal-dir` for explicit command-line inspection or a separate collection directory.
The dashboard daemon must read that same collection directory to display its contents.
Set `CLAWMETRY_ROBOTICS_DIR` for both the collector and ClawMetry when you use a custom directory.

The encrypted system snapshot includes an `asimov` summary from persisted evidence.
Cloud rendering uses the decrypted snapshot. The cloud server does not read robot files.
The local view can also consume an injected snapshot or a shared data provider.
Hosted history depends on the existing cloud connection and available evidence.

No motion, pause, emergency stop, media recording, odometry, or full-body reconstruction is included.
Use Menlo's documented controls to operate the robot.

The journal accepts events up to 64 KiB.
Each run has a 16 MiB limit. The shared journal directory has a 256 MiB limit.
The recorder reports dropped evidence when a limit is reached.
It does not delete old runs to make space.
Archive old evidence before you start another run if the journal is full.

## Sources

- [Menlo SDK source](https://github.com/menloresearch/menlo-sdk)
- [Menlo SDK reference](https://docs.menlo.ai/sdk/reference)
- [Menlo connection modes](https://docs.menlo.ai/sdk/connection-modes)
- [Asimov 1 hardware](https://github.com/menloresearch/asimov-1)
