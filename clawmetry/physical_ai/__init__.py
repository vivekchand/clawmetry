"""Shared, local-first Physical AI observation and opt-in task governance.

Ships in the ordinary ClawMetry wheel. Robot execution and physics libraries
belong to the robot's host, never to the dashboard process.
"""

from .governance import Decision, Request, Task, TaskGate
from .monitor import DeskMonitor
from .adapters.jumper import JumperObserver

__all__ = ["Decision", "Request", "Task", "TaskGate", "DeskMonitor", "JumperObserver"]
