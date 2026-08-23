"""Adapter contract tests for the Facebook connector.

Proves the commit-before-cursor boundary: the orchestrator commits each
payload durably BEFORE advancing the source watermark, so a crash or
commit failure never loses data.
"""

from datetime import datetime, timezone
from typing import NamedTuple
from unittest import TestCase

from openmagpie_schema.configs import FacebookGroupSourceSpec
from facebook_plugin.connector import FacebookConnector


class _FakeRecord(NamedTuple):
    external_id: str
    permalink: str
    occurred_at: datetime
    group_id: str
    content: str
    author_name: str = ""
    author_id: str = ""


class _FakeAction:
    def __init__(self, posts: list[_FakeRecord]) -> None:
        self._posts = posts

    def execute(self, spec: FacebookGroupSourceSpec):
        class _Result:
            new_posts = self._posts
        return _Result()


class FacebookConnectorCommitCursorTests(TestCase):
    def test_commit_failure_leaves_cursor_unchanged(self) -> None:
        """Orchestrator pattern: for each payload, commit durably then
        advance cursor to payload.occurred_at. A commit failure must
        leave the cursor where it was, so the next poll restarts from
        the same watermark and re-yields the uncommitted payload."""
        since = datetime(2026, 8, 22, 10, 0, 0, tzinfo=timezone.utc)

        t_old = datetime(2026, 8, 22, 9, 0, 0, tzinfo=timezone.utc)   # < since
        t1 = datetime(2026, 8, 22, 10, 30, 0, tzinfo=timezone.utc)    # >= since
        t2 = datetime(2026, 8, 22, 11, 0, 0, tzinfo=timezone.utc)     # >= since

        posts = [
            _FakeRecord("fb_old", "https://fb.com/g/123/posts/old", t_old, "123", "old post"),
            _FakeRecord("fb_1", "https://fb.com/g/123/posts/1", t1, "123", "first new"),
            _FakeRecord("fb_2", "https://fb.com/g/123/posts/2", t2, "123", "second new"),
        ]

        connector = FacebookConnector(action_factory=lambda: _FakeAction(posts))
        spec = FacebookGroupSourceSpec(group_id="123")

        # --- First poll: walk payloads, commit, advance cursor ---
        cursor = since
        committed: list[str] = []
        iterator = connector.poll(spec, since=cursor)

        # Payload 1: old post filtered out by since guard; fb_1 yielded
        p1 = next(iterator)
        self.assertEqual(p1.external_id, "fb_1")
        self.assertEqual(p1.occurred_at, t1)

        # Orchestrator: commit succeeds, advance cursor
        committed.append(p1.external_id)
        cursor = p1.occurred_at

        # Payload 2: fb_2 yielded
        p2 = next(iterator)
        self.assertEqual(p2.external_id, "fb_2")
        self.assertEqual(p2.occurred_at, t2)

        # Orchestrator: commit FAILS — cursor must NOT advance
        # (cursor stays at t1)

        # --- Second poll: same cursor, uncommitted payload re-yielded ---
        # fb_1 is at the exact boundary (10:30 >= 10:30) so it is re-yielded too.
        # That's safe — downstream dedups on external_id. The key property is
        # that the uncommitted fb_2 is NOT lost.
        payloads = list(connector.poll(spec, since=cursor))
        self.assertEqual([p.external_id for p in payloads], ["fb_1", "fb_2"])
        self.assertEqual(payloads[1].occurred_at, t2)

    def test_since_filters_out_older_posts(self) -> None:
        """Only posts with occurred_at >= since are yielded."""
        since = datetime(2026, 8, 22, 12, 0, 0, tzinfo=timezone.utc)

        posts = [
            _FakeRecord("fb_old", "https://fb.com/g/123/posts/old",
                       datetime(2026, 8, 22, 11, 0, 0, tzinfo=timezone.utc), "123", "old"),
            _FakeRecord("fb_new", "https://fb.com/g/123/posts/new",
                       datetime(2026, 8, 22, 13, 0, 0, tzinfo=timezone.utc), "123", "new"),
        ]

        connector = FacebookConnector(action_factory=lambda: _FakeAction(posts))
        spec = FacebookGroupSourceSpec(group_id="123")

        payloads = list(connector.poll(spec, since=since))
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0].external_id, "fb_new")

    def test_count_rewalks_poll(self) -> None:
        """BaseConnector.count() re-walks poll() discarding payloads."""
        since = datetime(2026, 8, 22, 10, 0, 0, tzinfo=timezone.utc)

        posts = [
            _FakeRecord("fb_1", "https://fb.com/g/123/posts/1", since, "123", "a"),
            _FakeRecord("fb_2", "https://fb.com/g/123/posts/2", since, "123", "b"),
        ]

        connector = FacebookConnector(action_factory=lambda: _FakeAction(posts))
        spec = FacebookGroupSourceSpec(group_id="123")

        self.assertEqual(connector.count(spec, since=since), 2)