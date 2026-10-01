# Local assessment privacy

The assessment privacy component protects a bounded request on the device
before a transport receives its bytes. It is a reusable primitive. Installing
it does not enable external assessments, change existing transcript scoring,
or send evidence anywhere.

The caller must first select the minimum evidence for a declared task. A
privacy policy then specifies the identifier coverage that task requires.
Masking is mandatory for this path, even when ordinary ingestion redaction
has been disabled. Errors stop dispatch; there is no raw-text fallback.

## Coverage

The initial detector reuses the locally tested formats in
`clawmetry/redaction.py`. This initial policy accepts ASCII payloads declared
as English; non-ASCII text and unsupported declared languages stop the request.

| Category | Tested format |
| --- | --- |
| Email | ASCII address with a dotted domain |
| Phone | International number beginning with `+`, 8 to 15 digits |
| Payment card | Recognized issuer prefix and length with a valid Luhn checksum |
| IBAN | Known country length and valid mod-97 checksum, including mixed/lowercase and grouped forms |
| National identifier | Dashed US SSN, UK NINO (case-insensitive), Indian Aadhaar and Dutch BSN, using the existing structural/checksum checks |

This is identifier masking, not anonymity. Names, street addresses, local
phone formats, Unicode email addresses and identifying context in arbitrary
prose are not covered. A policy requiring unsupported categories or languages
is rejected. Do not select a weaker policy just to send a richer transcript.
The evidence selector and the eventual assessment task must agree on the
required coverage before that task can be enabled.

Detected secrets are removed before personal identifiers are masked. Secret
values, including structured secret containers, cannot be restored. Existing
irreversible redactions remain irreversible; the component cannot recover
information already removed from stored history.

## Request and restoration boundaries

Every request field is traversed, including dictionary keys, state, questions,
rubrics and metadata. Unsupported objects, invalid numbers, excessive nesting,
oversized input and exceeded scan deadlines stop the request. Colliding
sanitized keys are rejected instead of losing or overwriting evidence.

Default limits are 64 KiB for the complete JSON request, 4,096 ASCII
characters in a single string and 320 characters in an unbroken word or
identifier. The map holds at most 256 distinct identifiers by default.
Oversized strings and candidate identifiers are rejected in full. Bounded,
overlapping scan windows preserve complete identifiers across their edges.
Ambiguous card or phone candidates containing a valid separated prefix stop
the request rather than exposing a partial identifier or guessing its end.

Within a request, equal detected identifiers receive the same opaque token.
Other requests have independently randomized tokens. The restoration map
remains in memory on the device and is discarded on close or expiry. It must
never enter a log, queue, database, prompt or snapshot, including an encrypted
assessment snapshot.

Restoration is only for explicitly permitted local display fields and the
matching scope. It makes one substitution pass over exact issued tokens and
escapes display output. Unknown tokens remain masked. A closed or expired map
does not guess original values. Labels, scores and other typed results do not
need restoration. A caller must retain the masked result for storage and
transport, keeping a restored rendering separate.

## Dispatch and consent

The dispatch boundary hands the transport only canonical masked JSON bytes.
Each attempt rechecks the consent generation and policy, request lifetime and
the existing offline/self-hosted egress restrictions. Revocation serializes
with dispatch: it stops later attempts, while a send already in progress must
be reported as already started. Transport implementations must use bounded
timeouts so revocation cannot wait indefinitely for network completion.

This component does not supply an evidence worker, hosted inference endpoint,
consent screen or provider integration. Those callers must use this boundary
for every first attempt, retry and fallback before managed assessments can be
activated. Tests of the local component are not evidence of a completed
provider assessment or verified agent recovery.

Normal cloud snapshots retain their existing encryption boundary. Any future
managed assessment service necessarily processes the sanitized request and
must disclose that separate boundary before consent. It receives neither the
restoration map nor the node's snapshot encryption key.
