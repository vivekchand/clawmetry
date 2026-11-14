# Node activity

Node activity shows observations from the machine or container where the ClawMetry daemon runs. It stays node-wide when you select an agent runtime.

Observe shows resource measurements, visible processes, listening sockets, available login records and changes to selected sensitive settings. Select a recorded change to inspect its before and after evidence. Replay follows recorded observations; it does not reconstruct every instruction that ran.

Govern lets you choose monitoring sources and review rules. A review marks one recorded event as expected or requiring investigation. It preserves the original evidence and does not approve future activity. Turning monitoring off stops collection and keeps prior history.

Guard groups changes that match enabled review rules. A new listener or changed setting is a reason to review the evidence, not proof of an attack. An unattributed process stays unattributed. The tab does not terminate arbitrary processes. Existing agent Guard controls retain their own session identity and permission checks.

## Coverage

The first version uses periodic observations through [psutil](https://psutil.io/). It can miss short-lived processes and changes between observations. A listening socket does not prove internet reachability. A login record does not establish who is at the keyboard. Resource usage does not identify an AI agent.

Each source reports its own time, scope and completeness. Permission failures and response limits produce partial or unavailable coverage. On macOS, system socket enumeration normally requires elevated permissions. On Linux, a restricted process can receive an incomplete socket list without an error. ClawMetry reports these limitations rather than treating missing rows as confirmed removals. It does not request privilege elevation or install a privileged sensor.

The initial scan establishes a baseline. It does not certify a clean machine. Comparison uses process start identity as well as PID and only infers removals from comparable complete sources. Restricted or container scope is shown explicitly.

Selected configuration files are fingerprinted locally. The public response excludes file contents, fingerprints, process arguments and environment values. Cloud detail travels inside the existing encrypted node snapshot. Hosted monitoring choices and reviews use a sealed request and require node confirmation before showing success.

## Further protection

Complete execution, file-read and connection attribution requires event sensors with appropriate permissions. Linux eBPF or audit, macOS Endpoint Security, Windows ETW and maintained endpoint security products are potential sources for later integrations. Prevention requires a separate verified enforcement boundary. The Node activity tab does not promise complete endpoint detection or prevention.
