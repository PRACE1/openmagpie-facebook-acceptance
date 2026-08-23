"""Runtime wiring verification for Facebook connector.
Run with: python verify_wiring.py (after setting env vars)
"""

import os
import sys

# Django setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps", "core"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings.base")

import django
django.setup()

# ── 1. Payload registry ──────────────────────────────────────────────
from sources import payload_registry

registered = payload_registry.registered()
payload_kinds = {kind for (_, kind) in registered}
print("Payload kinds registered:", sorted(payload_kinds))

assert "facebook_post" in payload_kinds, "facebook_post payload NOT registered"
print("✓ Payload registry: facebook_post registered")

# ── 2. Connector class ───────────────────────────────────────────────
from facebook_plugin.connector import FacebookConnector
from sources.connectors.base import BaseConnector

assert issubclass(FacebookConnector, BaseConnector), "FacebookConnector must inherit BaseConnector"
assert FacebookConnector.kind == "facebook_posts", f"kind mismatch: {FacebookConnector.kind}"
print("✓ Connector class: FacebookConnector(kind='facebook_posts', BaseConnector)")

# ── 3. Spec schema ───────────────────────────────────────────────────
from openmagpie_schema.configs import FacebookGroupSourceSpec
from openmagpie_schema.feed import SourceInput

spec = FacebookGroupSourceSpec(group_id="305056891435827", limit=25)
assert spec.kind == "facebook_posts"
assert spec.SOURCE_KIND == "facebook_posts"
print("✓ Spec schema: FacebookGroupSourceSpec validates directly")

# Prove it validates through the discriminated union via SourceInput
source_input = SourceInput.model_validate({
    "spec": {"kind": "facebook_posts", "group_id": "305056891435827"},
})
assert isinstance(source_input.spec, FacebookGroupSourceSpec)
assert source_input.spec.group_id == "305056891435827"
print("✓ Spec schema: FacebookGroupSourceSpec validates through SourceInput union")

# ── 4. Connector registry (orchestrator dispatch) ────────────────────
from sources import registry as connector_registry

# Try to look up the connector by source kind
connector = connector_registry.get("facebook_posts")
assert connector is not None, "facebook_posts connector NOT found in registry"
assert isinstance(connector, FacebookConnector), f"Wrong connector type: {type(connector)}"
print("✓ Connector registry: facebook_posts → FacebookConnector")

# ── 5. Poll signature ────────────────────────────────────────────────
import inspect
sig = inspect.signature(connector.poll)
params = list(sig.parameters.keys())
assert "spec" in params and "since" in params, f"poll() missing params: {params}"
print("✓ Poll signature: spec, since present")

print("\n" + "=" * 50)
print("ALL WIRING CHECKS PASSED")
print("=" * 50)