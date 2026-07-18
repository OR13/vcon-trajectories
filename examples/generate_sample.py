"""Generate a publishable example vCon from a synthetic Mythos-Agent record.

The input record (``mythos_agent_sample_record.json``) is hand-authored with
original content but uses the *exact same schema* as the gated
``VINAY-UMRETHE/Mythos-Agent`` dataset, and is converted with the *same*
``mythos.record_to_vcon`` used for the real rows. The resulting vCon is therefore
structurally identical to the ones derived from the gated data, but contains no
gated content and is safe to publish.

    PYTHONPATH=src python examples/generate_sample.py
"""
import json
import os

from vcon_trajectories.mythos import record_to_vcon
from vcon_trajectories.validate import make_validator, validate_vcon

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    with open(os.path.join(HERE, "mythos_agent_sample_record.json"), encoding="utf-8") as f:
        record = json.load(f)

    vcon = record_to_vcon(record)
    errors = validate_vcon(vcon, make_validator())
    if errors:
        print("INVALID:", *errors, sep="\n  ")
        return 1

    out = os.path.join(HERE, "mythos_agent_sample.vcon.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(vcon, f, indent=2, ensure_ascii=False)
    print(f"valid vCon 0.4.0 with {len(vcon['dialog'])} dialogs, "
          f"{len(vcon['parties'])} parties -> {os.path.relpath(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
