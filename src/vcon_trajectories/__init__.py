"""Represent Mythos agent trajectories as IETF vCons (draft-ietf-vcon-vcon-core, v0.4.0)."""

from .models import ToolCall, Round, Trajectory

__all__ = ["ToolCall", "Round", "Trajectory"]

VCON_VERSION = "0.4.0"
