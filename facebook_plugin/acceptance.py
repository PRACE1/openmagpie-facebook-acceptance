r"""Live acceptance test for FacebookConnector.

Usage:
    .venv\Scripts\python.exe -m facebook_plugin.acceptance 305056891435827
"""
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

# Ensure apps/core is on the path so 'sources.*' and 'openmagpie_schema.*' resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "core"))

from facebook_plugin.connector import FacebookConnector
from facebook_plugin.factory import make_action_factory
from openmagpie_schema.configs import FacebookGroupSourceSpec


def main(group_id: str, output_path: str | None = None) -> None:
    if output_path is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = f"live_acceptance_{group_id}_{ts}.json"

    connector = FacebookConnector(
        action_factory=make_action_factory(
            storage_state_path=r"C:\Users\R5 5600 GT\fb_cookies_playwright.json",
            headless=False,
        )
    )

    spec = FacebookGroupSourceSpec(group_id=group_id, limit=5)

    print(f"Starting live acceptance run for group {group_id}...")
    print("This will launch a real browser via Camofox. Wait 30-90 seconds.")
    print("-" * 50)

    since = None
    records = []
    error_info = None

    try:
        for payload in connector.poll(spec, since=since):
            records.append(payload)
            print(f"  captured: {payload.external_id}")
    except Exception as exc:
        error_info = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        print(f"  error: {type(exc).__name__}: {exc}")

    artifact = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "group_id": group_id,
        "since": since.isoformat() if since else None,
        "record_count": len(records),
        "records": [r.model_dump() for r in records],
        "error": error_info,
        "provenance": {
            "source": "facebook_camofox_client",
            "method": "posts.listen",
            "storage_state_path": r"C:\Users\R5 5600 GT\fb_cookies_playwright.json",
            "storage_state_exists": Path(r"C:\Users\R5 5600 GT\fb_cookies_playwright.json").exists(),
            "connector_kind": connector.kind,
            "connector_module": "facebook_plugin.connector",
        },
    }

    Path(output_path).write_text(json.dumps(artifact, indent=2, default=str))
    print("-" * 50)
    print(f"Wrote {len(records)} records to {output_path}")

    if records:
        print("\nFirst record preview:")
        print(json.dumps(records[0].model_dump(), indent=2, default=str))
    elif error_info is None:
        print("\nNo records returned and no error raised. Possible causes:")
        print("  - Cookie file expired (re-export from browser)")
        print("  - Group is private / you lack access")
        print("  - Facebook served a challenge page")
        print("  - No posts found in the requested group")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m facebook_plugin.acceptance <group_id> [output_path]")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)