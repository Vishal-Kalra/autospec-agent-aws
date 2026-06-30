"""CLI entry point: python -m autospec

Runs the full pipeline with the built-in demo brief and streams output to the console.
"""
from __future__ import annotations

import sys
from autospec.models import Brief, RunConfig
from autospec.orchestrator import Orchestrator

DEMO_BRIEF = Brief(
    "Build a tip calculator that takes a bill total, a tip percentage, and a number of "
    "people, and returns the tip amount, the total with tip, and the amount each person "
    "owes. Round money to 2 decimal places. 0% tip is allowed. People must be >= 1."
)
DEFAULT_CONFIG = RunConfig(tech_stack="Python", quality_threshold=90)


def main():
    print("\n⚡ AutoSpec — Multi-Agent AI Pipeline")
    print("=" * 50)

    def emit(event_type: str, data: dict):
        agent = data.get("agent", "")
        if event_type == "agent_start":
            print(f"\n🔄 [{agent}] Starting...")
        elif event_type == "agent_output":
            print(f"✅ [{agent}] {data.get('summary', '')}")
        elif event_type == "handoff":
            print(f"   ➡️  {data['from']} → {data['to']}")
        elif event_type == "verdict":
            icon = "✅" if data["verdict"] == "ALIGNED" else "❌"
            print(f"\n{icon} VERDICT: {data['verdict']}")
            print(f"   Coverage: {data.get('coverage', 0)}% | Gate: {data.get('quality_gate', '?')}")
            if data.get("gaps"):
                for g in data["gaps"]:
                    print(f"   ⚠️  Gap [{g['id']}]: {g['desc']}")
        elif event_type == "reattempt":
            print(f"\n🔄 RE-ATTEMPT {data['attempt']}/{data['limit']}")
        elif event_type == "pipeline_done":
            print(f"\n{'=' * 50}")
            print(f"🏁 Pipeline: {data.get('status', 'done')}")
        elif event_type == "artifact_saved":
            print(f"   💾 Saved: {data['name']}")
        elif event_type == "error":
            print(f"   ❌ Error: {data.get('message', '')}")

    import os
    from datetime import datetime
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    artifact_dir = os.path.join(os.getcwd(), "artifacts", run_id)

    orch = Orchestrator(artifact_dir=artifact_dir, emit=emit)
    result = orch.run(DEMO_BRIEF, DEFAULT_CONFIG)

    print(f"\n📦 Artifacts saved to: {artifact_dir}/")
    print(f"   Files: {', '.join(sorted(os.listdir(artifact_dir)))}")
    print()


if __name__ == "__main__":
    main()
