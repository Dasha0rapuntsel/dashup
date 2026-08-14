"""CLI entry point for the SafeDesk AI proof of concept."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from src.safedesk.pipeline import SupportPipeline, Ticket


ROOT = Path(__file__).resolve().parent


def build_pipeline(audit_path: Path | None = None) -> SupportPipeline:
    return SupportPipeline(
        kb_path=ROOT / "data" / "kb.json",
        audit_path=audit_path or ROOT / ".runtime" / "audit.jsonl",
    )


def run_demo(pipeline: SupportPipeline) -> list[dict]:
    tickets = [
        Ticket("DEMO-HAPPY", "web", "Как отключить email-уведомления?"),
        Ticket(
            "DEMO-RISKY",
            "chat",
            "С карты списали деньги дважды. Номер карты 4111 1111 1111 1111, верните деньги.",
        ),
    ]
    results = [pipeline.process(ticket).to_dict() for ticket in tickets]
    assert results[0]["action"] == "AUTO_CLOSE"
    assert results[1]["action"] == "ESCALATE"
    assert "4111 1111" not in json.dumps(results[1], ensure_ascii=False)
    return results


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="SafeDesk AI ticket routing PoC")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--demo", action="store_true", help="run happy and risky paths")
    group.add_argument("--text", help="ticket text")
    parser.add_argument("--ticket-id", default="CLI-1")
    parser.add_argument("--channel", default="web", choices=["web", "chat", "email", "mobile"])
    parser.add_argument("--audit-log", type=Path)
    args = parser.parse_args()

    pipeline = build_pipeline(args.audit_log)
    if args.demo:
        payload = run_demo(pipeline)
    else:
        payload = pipeline.process(Ticket(args.ticket_id, args.channel, args.text or "")).to_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
