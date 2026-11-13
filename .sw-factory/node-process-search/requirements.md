# Process search and ClawMetry resource visibility

## Overview

A user could not find ClawMetry in the Node process list or determine its resource use. The list shows only 100 CPU-ranked rows and operating-system names such as python3.12. Users need to find any retained process and inspect the cost of monitoring itself.

## Terminology

Retained process: a current or explicitly stale observation stored by the collector.\
ClawMetry process: the collector itself or a process with a recognized ClawMetry executable, module or installed script entry point. This identifies software, not the person who started it.

## Requirements

### REQ-OBS-NODE-SEARCH-001: Find processes

As a node owner, I want to search the process list so that I can find a program without scrolling through unrelated programs.

* AC-OBS-NODE-SEARCH-001.1: When a user enters a process name or PID, the system shall filter all retained process rows, regardless of the visible page.
* AC-OBS-NODE-SEARCH-001.2: When results exceed one page, the system shall offer navigation and show the result count. Clearing search shall restore the list.
* AC-OBS-NODE-SEARCH-001.3: When observations refresh, the system shall preserve the search text without an additional network request for search.

### REQ-OBS-NODE-SEARCH-002: Inspect monitoring resource use

As a node owner, I want to see ClawMetry CPU and memory so that I can assess monitoring overhead.

* AC-OBS-NODE-SEARCH-002.1: When collection succeeds, the system shall retain the collector process within the process budget even if normal enumeration omits it.
* AC-OBS-NODE-SEARCH-002.2: When a recognized ClawMetry process is observed, the system shall show its role, PID, CPU and resident memory in a dedicated section and include it in searches for ClawMetry.
* AC-OBS-NODE-SEARCH-002.3: When readings are incomplete, stale, disabled or unavailable, the system shall state that condition and shall not present an incomplete sum as total usage.
* AC-OBS-NODE-SEARCH-002.4: When process metadata is persisted or synchronized, the system shall omit command lines, environments and argument values while retaining role and measurement metadata.

## Non-goals, alternatives and risks

No new poller, no process controls, no claim that the process list covers the entire host, and no proportional/shared-memory estimate. Memory is RSS and can count shared pages more than once across processes. No lifetime-average CPU. Searching raw command lines was rejected because arguments can contain secrets. Raising the visible row cap alone was rejected because it still makes discovery difficult. Search filters only retained observations, and the UI says so. Recognition uses exact entry points rather than arbitrary substrings; unrecognized or inaccessible processes stay unlabeled. Rollback removes additive role metadata and UI without a schema migration.

### REQ-OBS-NODE-SEARCH-003: Live measurements

As a node owner, I want changing CPU and memory measurements while I watch the Node view, so that I can inspect activity as I would in htop. The live incident showed a 139-second ingest cycle invalidating the CPU comparison interval.

* AC-OBS-NODE-SEARCH-003.1: When the Node view is visible and active, the system shall sample and display process CPU and memory about every two seconds independently of slow ingest or startup backfill.
* AC-OBS-NODE-SEARCH-003.2: When the view is hidden or left, the browser shall stop its live requests and the collector shall return to a slower cadence after a bounded viewing lease expires.
* AC-OBS-NODE-SEARCH-003.3: When live readings arrive, the system shall preserve the search text and distinguish fresh measurements, initial sampling, delayed updates and snapshot fallback.
* AC-OBS-NODE-SEARCH-003.4: When viewed through cloud, the system shall deliver the live measurements as encrypted bounded frames through the existing authenticated cache and relay, without increasing full system-snapshot frequency.

The cadence correction replaces ingest-loop collection with one independent daemon worker. Full listener/settings/history work remains on a 30-second cadence. Only bounded process/resource frames use the two-second viewing cadence. Cloud publication uses a bounded latest-frame queue; network work cannot delay measurement. No host collection occurs in a request handler.
