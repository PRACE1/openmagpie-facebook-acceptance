import asyncio
import sys
from datetime import datetime, timezone
from typing import Iterator

from sources.connectors.base import BaseConnector
from facebook_plugin.factory import make_action_factory
from facebook_plugin.payloads import FacebookPostPayload
from openmagpie_schema.configs import FacebookGroupSourceSpec


class FacebookConnector(BaseConnector):
    kind = "facebook_posts"
    payloads = [FacebookPostPayload]

    def __init__(self, action_factory=None, **kwargs):
        self._action_factory = action_factory or make_action_factory

    def poll(self, spec: FacebookGroupSourceSpec, since=None) -> Iterator[FacebookPostPayload]:
        from facebook_camofox_client.domain_actions.envelope import ActionEnvelope
        from facebook_camofox_client.domain_posts.schemas import PostsListenInput

        action = self._action_factory()
        envelope = ActionEnvelope(
            action_id="acceptance-test",
            action_type="posts.listen",
            account_id="test-account",
            input=PostsListenInput(group_id=spec.group_id, terms=[], limit=spec.limit or 10).model_dump(),
            idempotency_key="test-idempotency",
        )
        result = self._run_sync(action.execute(envelope))

        for post in result.new_posts:
            payload = FacebookPostPayload.from_record(post)
            if not self._is_valid(payload):
                continue
            # --- since guard (fixes the 2 remaining test failures) ---
            if since is not None and payload.occurred_at is not None and payload.occurred_at < since:
                continue
            yield payload

    @staticmethod
    def _is_valid(record) -> bool:
        if not getattr(record, "external_id", None):
            return False
        if not getattr(record, "permalink", None) and not getattr(record, "url", None):
            return False
        if not getattr(record, "occurred_at", None):
            return False
        if not getattr(record, "group_id", None):
            return False
        return True

    def _run_sync(self, coro):
        if not asyncio.iscoroutine(coro):
            return coro
        if sys.platform == "win32":
            old_policy = asyncio.get_event_loop_policy()
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                return asyncio.run(coro)
            finally:
                asyncio.set_event_loop_policy(old_policy)
        else:
            return asyncio.run(coro)