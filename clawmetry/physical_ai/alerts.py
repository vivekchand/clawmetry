"""Deliver known persisted robot findings through shared notification settings.

Only stable, fixed text leaves the node through the existing notification
channels. Raw task prompts, measurements and source messages stay in DuckDB.
"""
import logging

log = logging.getLogger(__name__)
_FINDINGS = {
    "boundary_approach": ("warning", "The robot is approaching its workspace boundary."),
    "boundary_crossed": ("critical", "The robot crossed its workspace boundary."),
    "unexpected_lift": ("warning", "The robot base rose unexpectedly."),
    "excessive_tilt": ("critical", "The robot tilt exceeds its configured limit."),
    "observation_lost": ("warning", "Robot observations are unavailable. Its outcome is unknown."),
    "task_boundary": ("warning", "A robot request was outside its allowed task."),
    "task_denied": ("warning", "A robot request was declined by its task policy."),
}


def dispatch(store, event):
    """Best-effort shared delivery after the journal transaction has committed."""
    try:
        from clawmetry.asimov.store import JUMPER_SOURCES, RUN_ID
        if not isinstance(event, dict) or event.get("kind") != "guard.incident":
            return None
        run_id = event.get("run_id")
        if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
            return None
        rows = store._fetch("SELECT source_kind,environment FROM asimov_runs WHERE run_id=?", [run_id])
        if not rows or rows[0][0] not in JUMPER_SOURCES:
            return None
        data = event.get("data")
        if not isinstance(data, dict):
            return None
        kind = data.get("kind", data.get("type"))
        if not isinstance(kind, str) or kind not in _FINDINGS:
            return None
        severity, title = _FINDINGS[kind]
        simulation = rows[0][1] == "simulation"
        recorded = rows[0][0] == "jumper_recording"
        qualifier = "Recorded simulation: " if recorded and simulation else "Recorded evidence: " if recorded else "Simulation: " if simulation else ""
        incident = {"session_id": "physical_ai:" + run_id, "kind": "physical_ai_" + kind,
                    "severity": severity, "runtime": "jumper",
                    "title": qualifier + title,
                    "detail": "Review the recorded Physical AI evidence. This alert does not confirm a physical stop.",
                    "evidence": []}
        from clawmetry.incident_alerts import deliver_incident
        return deliver_incident(store, incident, source="physical_ai")
    except Exception:
        log.warning("Physical AI alert delivery could not finish")
        return None
