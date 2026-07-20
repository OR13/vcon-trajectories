"""Multi-source trajectory adapters.

Each real dataset has its own record shape; every adapter in `adapters.py`
normalizes a raw record into the shared intermediate representation in `ir.py`
(`UTrajectory` / `Turn`). A single converter, `ir.utrajectory_to_vcon`, maps the
IR to a vCon 0.4.0 core object, so the source-specific code stays small and the
trajectory→vCon mapping lives in exactly one place.
"""

from .ir import Turn, UTrajectory, utrajectory_to_vcon

__all__ = ["Turn", "UTrajectory", "utrajectory_to_vcon"]
