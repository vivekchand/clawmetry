## Overview
Users should be able to open ClawMetry, ask about their setup and agent usage, and receive an answer with interactive visuals grounded in their own recorded data. Follow-up questions refine the analysis; saved panels remain on their dashboard.
## Terminology
Panel: a chart, table, or metric backed by a validated read-only local query.
Harness: an installed authenticated agent CLI used to generate answers.
## Requirements
REQ-ASSIST-001: Conversational opening. As an operator I want typed or voice questions so I can explore without learning navigation. AC-ASSIST-001.1: On opening the dashboard the system shall show an accessible chat composer. AC-ASSIST-001.2: On explicit microphone activation the system shall transcribe for review and handle denial or unavailable speech support.
REQ-ASSIST-002: Grounded visuals. As an operator I want real charts and evidence so I can verify an answer. AC-ASSIST-002.1: On a visual request the system shall render up to four validated charts, metrics or tables from local DuckDB. AC-ASSIST-002.2: Missing observations and query failures shall be identified, never fabricated. AC-ASSIST-002.3: Follow-ups shall use recent conversation context.
REQ-ASSIST-003: Persistence. As an operator I want saved conversations and panels so I can return later. AC-ASSIST-003.1: Saved conversations and dashboard definitions shall survive page reload in DuckDB. AC-ASSIST-003.2: Saved panels shall refresh from current data.
REQ-ASSIST-004: Provider choice. As an operator I want to reuse my harness or API credential. AC-ASSIST-004.1: The system shall detect the supported authenticated local harness and accept an optional request-scoped provider key. AC-ASSIST-004.2: Credentials shall not be returned, logged, or saved in conversations. AC-ASSIST-004.3: Managed credit status shall reflect an authenticated ledger, or explicitly state that it is not connected.

## Hosted product record
Published and reloaded in the existing ClawMetry project:
https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/requirements/fb690e36-8372-48f6-8e52-32fe5bffc345
