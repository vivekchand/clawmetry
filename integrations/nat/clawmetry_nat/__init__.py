"""
clawmetry-nat — NVIDIA NeMo Agent Toolkit telemetry exporter for ClawMetry.

Maps NAT IntermediateStep events to ClawMetry brain event format and ships
them to the ClawMetry ingest endpoint (or JSONL files locally).

Quick start:
    from clawmetry_nat import ClawMetryNATExporter
    exporter = ClawMetryNATExporter()
    exporter.on_event(nat_step)          # callback-style
"""

from .exporter import ClawMetryNATExporter
from .mapper import NATEventMapper

__version__ = "0.1.0"
__all__ = ["ClawMetryNATExporter", "NATEventMapper", "__version__"]
