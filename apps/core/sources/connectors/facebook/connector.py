"""Facebook connector — re-exports the canonical connector from facebook_plugin
and registers its payloads + connector instance with the runtime registries.
"""

from sources.payload_registry import register as register_payload
from sources.registry import register_source
from facebook_plugin.connector import FacebookConnector

__all__ = ["FacebookConnector"]

# Register payloads for FeedItem.data hydration
register_payload(FacebookConnector.kind, FacebookConnector.payloads)

# Register connector instance for orchestrator dispatch
register_source(FacebookConnector())