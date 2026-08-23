import sys
import traceback

sys.path.insert(0, "apps/core")
import django
django.setup()

from facebook_plugin.connector import FacebookConnector
from facebook_plugin.factory import make_action_factory
from openmagpie_schema.configs import FacebookGroupSourceSpec

connector = FacebookConnector(
    action_factory=make_action_factory(
        storage_state_path=r"C:\Users\R5 5600 GT\fb_cookies_playwright.json",
        headless=False,
    )
)
spec = FacebookGroupSourceSpec(group_id="305056891435827", limit=5)

try:
    records = list(connector.poll(spec, since=None))
    print(f"SUCCESS: {len(records)} records captured")
    for r in records:
        print(f"  - {r.external_id}: {r.content[:60]}...")
except Exception:
    traceback.print_exc()