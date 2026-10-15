"""Observe-only, data-only LiveKit connection using optional Menlo SDK 0.1.0."""

import math
import sys
import time

from .journal import JournalWriter
from .sdk import SdkObserver


# Importing this module must remain usable on ClawMetry's base Python floor.
# Version checks and Menlo imports belong inside explicit live operations.
def require_sdk():
    """Check Python and load Menlo when called; module import does neither."""
    if sys.version_info < (3, 12):
        raise RuntimeError(
            "Live Asimov collection needs Python 3.12 or newer. Import a recording on this Python, or use a separate Python 3.12 environment."
        )
    try:
        import menlo
        from menlo import asimov
    except ImportError as exc:
        raise RuntimeError(
            "Install the optional collector in Python 3.12 or newer: pip install 'menlo-sdk==0.1.0'. You can also use clawmetry asimov import-recording without it."
        ) from exc
    if menlo.__version__ != "0.1.0":
        raise RuntimeError(
            "The data-only observer is tested with menlo-sdk==0.1.0. Install that version in the collector environment."
        )
    return asimov


def data_only_client_class():
    """Explicitly load the live SDK and build a client without media subscriptions."""
    require_sdk()
    from menlo.asimov.transport._livekit_client import (
        _LiveKitClient,
        can_publish_data_from_token,
    )

    class DataOnlyClient(_LiveKitClient):
        # Adapted from Menlo SDK 0.1.0 _LiveKitClient._join, Apache-2.0,
        # Copyright 2026 Menlo Research Pte. Ltd. Source:
        # https://github.com/menloresearch/menlo-sdk/blob/v0.1.0/src/menlo/asimov/transport/_livekit_client.py
        # Data tracks subscribe independently; auto_subscribe controls media tracks.
        async def _join(self, rtc, token):
            if can_publish_data_from_token(token) is not False:
                raise RuntimeError(
                    "The observer requires an explicit Observe token without data publication authority"
                )
            room = rtc.Room()
            room.on("data_track_published", self._on_data_track_published)
            room.on("data_track_unpublished", self._on_data_track_unpublished)
            room.on("participant_attributes_changed", self._on_attributes_changed)
            room.on("disconnected", self._on_disconnected)
            await room.connect(
                self._url, token, options=rtc.RoomOptions(auto_subscribe=False)
            )
            self._room = room
            self._connected = True

    return DataOnlyClient


def observe_live(
    *,
    manager_url=None,
    credential=None,
    robot_id=None,
    directory=None,
    duration=None,
    environment="hardware",
    stop_event=None,
):
    """Check live dependencies here, then receive state without robot control."""
    sdk = require_sdk()
    if duration is not None and (
        not math.isfinite(duration) or duration <= 0 or duration > 86400
    ):
        raise ValueError("Duration must be positive and at most 86400 seconds")
    if manager_url is None or credential is None:
        try:
            config = sdk.ConnectionConfig.from_environment()
        except sdk.ConnectError as exc:
            raise ValueError(
                "No saved Asimov Observe connection is available. Set MENLO_MANAGER_URL and MENLO_CREDENTIAL, save an Observe connection with menlo setup, or use clawmetry asimov import-recording FILE --robot-id NAME."
            ) from exc
        manager = config.livekit
        if not isinstance(manager, sdk.ManagerConfig):
            raise ValueError(
                "Live observation needs an Asimov Manager Observe credential from menlo setup or MENLO_MANAGER_URL and MENLO_CREDENTIAL. Otherwise import a recording."
            )
        if (
            manager_url is not None
            and manager.url != sdk.ManagerConfig(manager_url, "unused").url
        ):
            raise ValueError(
                "Set MENLO_CREDENTIAL together with --manager-url. A saved credential is not sent to a different manager."
            )
        if credential is not None and manager.credential != credential:
            raise ValueError(
                "Set MENLO_MANAGER_URL together with MENLO_CREDENTIAL, or use the saved Observe connection."
            )
    else:
        manager = sdk.ManagerConfig(url=manager_url, credential=credential)
    grant = manager.check()
    if grant.role != "observe":
        raise ValueError(
            "Create an Observe credential in Asimov Manager. This collector refuses Control or unknown roles."
        )
    resolved = manager.resolve()
    if resolved.room != grant.room:
        raise ValueError(
            "Asimov Manager changed the robot room during connection. Retry observation."
        )
    client = data_only_client_class()(resolved.url, resolved.room, token=resolved.token)
    transport = sdk.LiveKitTransport(
        resolved.url,
        resolved.room,
        token=resolved.token,
        client=client,
        media_timeout=0.0,
    )
    robot = sdk.Robot(transport)
    writer = JournalWriter(
        robot_id or grant.room,
        "asimov_sdk",
        directory=directory,
        environment=environment,
        metadata={
            "source_scope": "passive_observer",
            "observation_only": True,
            "connection_mode": "livekit",
            "media_subscribed": False,
            "manager_room": grant.room,
            "credential_role": "observe",
            "complete_control_trace": False,
        },
    )
    observer = SdkObserver(
        robot,
        robot_id=robot_id or grant.room,
        trace_commands=False,
        writer=writer,
        source_scope="passive_observer",
    )
    started = time.monotonic()
    try:
        with observer:
            robot.open(timeout=10.0)
            while duration is None or time.monotonic() - started < duration:
                if stop_event is not None and stop_event.is_set():
                    break
                observer.check_freshness()
                if not robot.connected:
                    writer.emit(
                        "telemetry.lost", {"reason": "SDK connection is disconnected"}
                    )
                    break
                time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    except Exception:
        writer.emit(
            "telemetry.lost",
            {
                "reason": "Observe connection failed; check the robot and Observe credential"
            },
        )
        writer._loss("Observe connection failed")
        raise
    finally:
        # No velocity/trajectory was issued or held; closing only our observer releases its transport.
        robot.close()
        status = writer.close()
    return status
