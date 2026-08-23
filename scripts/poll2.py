"""
Poll 2: Real deduplication check against live Facebook group.
Uses since = max(occurred_at) from Poll 1.
"""
import sys
import os
import json
from datetime import datetime, timezone

# --- 1. Load Poll 1 evidence ---
EVIDENCE_FILE = r"C:\Users\R5 5600 GT\openmagpie\live_acceptance_305056891435827_20260823_133744.json"

with open(EVIDENCE_FILE, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# The JSON is a dict with a "records" key containing the posts
records = raw_data.get("records", [])

print(f"=== Poll 1 Evidence ===")
print(f"  File: {EVIDENCE_FILE}")
print(f"  Run at: {raw_data.get('run_at')}")
print(f"  Group: {raw_data.get('group_id')}")
print(f"  Records: {len(records)}")
print(f"  IDs: {[r.get('external_id') for r in records]}")

# --- 2. Compute cursor ---
occurred_ats = []
for r in records:
    val = r.get("occurred_at")
    if val:
        # Handle "2026-08-23 13:31:46+00:00" -> replace space with T for fromisoformat
        dt = datetime.fromisoformat(val.replace(" ", "T"))
        occurred_ats.append(dt)

since = max(occurred_ats)
print(f"  Max occurred_at (cursor): {since.isoformat()}")
print()

# --- 3. Set up Django ---
os.environ["DJANGO_SETTINGS_MODULE"] = "conf.settings.base"
os.environ["POSTGRES_PASSWORD"] = "dummy-postgres-pass"
os.environ["DJANGO_SECRET_KEY"] = "dummy-secret-for-tests"
os.environ["BASE_URL"] = "http://localhost:8000"
os.environ["APP_BASE_URL"] = "http://localhost:8000"
os.environ["MARKETING_BASE_URL"] = "http://localhost:8000"
os.environ["ENGINE_BASE_URL"] = "http://localhost:11434/v1"

sys.path.insert(0, r"C:\Users\R5 5600 GT\openmagpie\apps\core")
import django
django.setup()

# --- 4. Poll 2: Real browser, real session, real cursor ---
from facebook_plugin.connector import FacebookConnector
from facebook_plugin.factory import make_action_factory
from openmagpie_schema.configs import FacebookGroupSourceSpec

GROUP_ID = "305056891435827"
SESSION_PATH = r"C:\Users\R5 5600 GT\fb_cookies_playwright.json"

connector = FacebookConnector(
    action_factory=make_action_factory(
        storage_state_path=SESSION_PATH,
        headless=False,
    )
)
spec = FacebookGroupSourceSpec(group_id=GROUP_ID, limit=10)

print(f"=== Poll 2: Re-poll with since={since.isoformat()} ===")
print("Launching real browser via Camofox... (~30-90s)")
print("-" * 50)

yielded = list(connector.poll(spec, since=since))

print(f"Yielded records: {len(yielded)}")
for rec in yielded:
    print(f"  -> {rec.external_id} | {rec.occurred_at}")

print("-" * 50)
print()

# --- 5. Verdict ---
print("=" * 50)
if len(yielded) == 0:
    print("GATE 3 PASS")
    print("Zero duplicates returned. The since-guard works on real data.")
    print("Evidence chain: real browser -> real auth -> real extraction -> dedup verified.")
else:
    print(f"GATE 3 FAIL: {len(yielded)} records re-yielded (expected 0)")
print("=" * 50)
