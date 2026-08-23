import sys
import asyncio

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

print("Running poll with full diagnostics...")
print("=" * 50)

action = connector._action_factory()

async def run():
    from facebook_camofox_client.domain_actions.envelope import ActionEnvelope
    from datetime import datetime, timezone
    
    envelope = ActionEnvelope(
        action_id="poll",
        action_type="posts.listen",
        account_id="default",
        session_id=None,
        input={
            "group_id": spec.group_id,
            "limit": 5,
            "feed_mode": "recent",
            "terms": [],
        },
        idempotency_key=f"{spec.group_id}-{datetime.now(timezone.utc).isoformat()}",
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    
    result = await action.execute(envelope)
    
    print(f"Result type: {type(result).__name__}")
    print(f"Has .success: {hasattr(result, 'success')}")
    if hasattr(result, 'success'):
        print(f"  success = {result.success}")
    
    print(f"Has .error: {hasattr(result, 'error')}")
    if hasattr(result, 'error') and result.error:
        print(f"  error = {result.error}")
    
    print(f"Has .data: {hasattr(result, 'data')}")
    if hasattr(result, 'data') and result.data:
        data = result.data
        print(f"  data type: {type(data).__name__}")
        
        for attr in ['group_id', 'feed_mode', 'new_count', 'posts', 'cursor', 'coverage']:
            if hasattr(data, attr):
                val = getattr(data, attr)
                if attr == 'posts':
                    print(f"  data.{attr}: {len(val)} items")
                    if val:
                        print(f"    First post type: {type(val[0]).__name__}")
                elif attr == 'coverage':
                    print(f"  data.{attr}: {val}")
                else:
                    print(f"  data.{attr}: {val}")
            else:
                print(f"  data.{attr}: MISSING")
    else:
        print("  No data attribute")
    
    if hasattr(result, 'model_dump'):
        print("\n--- Full model_dump ---")
        import json
        dump = result.model_dump()
        print(json.dumps(dump, indent=2, default=str)[:3000])

# Windows: twikit sets SelectorEventLoop, but Playwright needs ProactorEventLoop
if sys.platform == "win32":
    old_policy = asyncio.get_event_loop_policy()
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        asyncio.run(run())
    finally:
        asyncio.set_event_loop_policy(old_policy)
else:
    asyncio.run(run())

print("=" * 50)
print("Diagnostics complete.")