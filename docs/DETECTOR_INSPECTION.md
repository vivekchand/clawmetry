# Credential inspection and its limits

Guard inspects the tool arguments and results delivered by runtime adapters.
It recognizes supported credential shapes in plaintext, percent encoding,
standard and URL-safe Base64, hexadecimal, and escaped Unicode/bytes. These
transformations can be nested. Decoded text is inspected as data; nothing is
executed or fetched. Results retain their original case for decoding, even
though failure detection uses a separate, short, lowercase preview.

The [public Hugging Face swarm traces](https://swarmtraces.org/) motivate this
work: a GET request can carry data in its URL, and visible commands can conceal
their contents behind encodings. A GET-only tool is not a data-loss boundary.
These detectors report observations and correlations, not proof of successful
transmission. The independent Pipelock fixtures already vendored in this repo
are also replayed through encoded transformations and benign near-misses.

Each payload has fixed inspection budgets:

| Resource | Limit |
| --- | ---: |
| Original string characters across a payload | 65,536 |
| Original plus decoded characters | 131,072 |
| Inspected string views | 128 |
| Base64/hex decode candidates, including rejected candidates | 128 |
| Nested decode transformations | 4 |
| Container nodes | 512 |
| Container depth | 8 |

Exceeding a budget creates an informational `inspection_incomplete` finding.
It contains counts and reason codes, never raw content. This is a coverage gap,
not an accusation. A normal command can reach a limit, particularly when it
contains a large document or many encoded strings. An absent finding does not
certify safety or completeness of other detectors.

Credential evidence keeps categories and sanitized destinations. Userinfo,
URL paths, queries, and fragments are excluded; recognized credential host
labels are redacted. Dot-separated credentials can require redacting the whole
host. Exact documented example tokens and single-character placeholder bodies
are excluded, but adding a word such as `example` to a varied token does not
suppress detection.

Interpreter heredocs remain in the executable command surface. Document-only
heredoc bodies are excluded from that surface, but still inspected for credential
values. This is a bounded heuristic over recorded commands, not a shell parser
or a syscall trace.

These checks cannot see events an adapter never supplies, establish that local
logs were not altered, inspect arbitrary encryption, reconstruct arbitrary
cross-request fragments, or prevent a privileged process disabling collection.
Effective containment additionally requires independently enforced network,
filesystem and credential boundaries. Observation remains the default; this
change does not enable blocking or change an operator's existing policies.
