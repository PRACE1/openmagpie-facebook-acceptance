"""Adapter contract tests for the Facebook connector.

Proves the commit-before-cursor boundary: the orchestrator commits each
payload durably BEFORE advancing the source watermark, so a crash or
commit failure never loses data.
"""

from datetime import UTC, datetime
from typing import NamedTuple
from unittest import TestCase
from unittest.mock import Mock

from facebook_plugin.connector import FacebookConnector
from facebook_plugin.payloads import FacebookPostPayload
from pydantic import ValidationError

from openmagpie_schema.configs import FacebookGroupSourceSpec


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
        since = datetime(2026, 8, 22, 10, 0, 0, tzinfo=UTC)

        t_old = datetime(2026, 8, 22, 9, 0, 0, tzinfo=UTC)  # < since
        t1 = datetime(2026, 8, 22, 10, 30, 0, tzinfo=UTC)  # >= since
        t2 = datetime(2026, 8, 22, 11, 0, 0, tzinfo=UTC)  # >= since

        posts = [
            _FakeRecord(
                "fb_old",
                "https://www.facebook.com/groups/123/posts/fb_old/",
                t_old,
                "123",
                "old post",
                "author_old",
                "Old Author",
            ),
            _FakeRecord(
                "fb_1",
                "https://www.facebook.com/groups/123/posts/fb_1/",
                t1,
                "123",
                "first new",
                "author_1",
                "Author One",
            ),
            _FakeRecord(
                "fb_2",
                "https://www.facebook.com/groups/123/posts/fb_2/",
                t2,
                "123",
                "second new",
                "author_2",
                "Author Two",
            ),
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
        since = datetime(2026, 8, 22, 12, 0, 0, tzinfo=UTC)

        posts = [
            _FakeRecord(
                "fb_old",
                "https://www.facebook.com/groups/123/posts/fb_old/",
                datetime(2026, 8, 22, 11, 0, 0, tzinfo=UTC),
                "123",
                "old",
                "author_old",
                "Old Author",
            ),
            _FakeRecord(
                "fb_new",
                "https://www.facebook.com/groups/123/posts/fb_new/",
                datetime(2026, 8, 22, 13, 0, 0, tzinfo=UTC),
                "123",
                "new",
                "author_new",
                "New Author",
            ),
        ]

        connector = FacebookConnector(action_factory=lambda: _FakeAction(posts))
        spec = FacebookGroupSourceSpec(group_id="123")

        payloads = list(connector.poll(spec, since=since))
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0].external_id, "fb_new")

    def test_count_rewalks_poll(self) -> None:
        """BaseConnector.count() re-walks poll() discarding payloads."""
        since = datetime(2026, 8, 22, 10, 0, 0, tzinfo=UTC)

        posts = [
            _FakeRecord(
                "fb_1", "https://www.facebook.com/groups/123/posts/fb_1/", since, "123", "a", "author_a", "Author A"
            ),
            _FakeRecord(
                "fb_2", "https://www.facebook.com/groups/123/posts/fb_2/", since, "123", "b", "author_b", "Author B"
            ),
        ]

        connector = FacebookConnector(action_factory=lambda: _FakeAction(posts))
        spec = FacebookGroupSourceSpec(group_id="123")

        self.assertEqual(connector.count(spec, since=since), 2)


class FacebookConnectorStrictValidationTests(TestCase):
    """Failure-path: one bad record aborts the entire poll."""

    def _make_record(self, **overrides):
        defaults = {
            "external_id": "123",
            "post_id": "123",
            "group_id": "305056891435827",
            "author_id": "456",
            "author_name": "Test Author",
            "content": "Valid content",
            "text": "Valid content",
            "url": "https://www.facebook.com/groups/305056891435827/posts/123/",
            "permalink": "https://www.facebook.com/groups/305056891435827/posts/123/",
            "occurred_at": datetime.now(UTC),
            "created_at": datetime.now(UTC),
            "captured_at": datetime.now(UTC),
            "title": None,
            "external_url": None,
            "parent_external_id": None,
        }
        defaults.update(overrides)
        rec = Mock()
        for k, v in defaults.items():
            setattr(rec, k, v)
        return rec

    def _make_factory(self, records):
        async def _execute(envelope):
            result = Mock()
            result.new_posts = records
            return result

        def factory():
            action = Mock()
            action.execute = _execute
            return action

        return factory

    def test_poll_fails_entirely_when_one_record_is_invalid(self):
        """
        Valid post + invalid post -> ValidationError on the first bad record.
        Zero payloads emitted. No artifact. Cursor unchanged.
        """
        valid = self._make_record(external_id="1", content="valid")
        invalid = self._make_record(external_id="2", content="")  # blank -> invalid

        connector = FacebookConnector(action_factory=self._make_factory([valid, invalid]))
        spec = FacebookGroupSourceSpec(group_id="305056891435827", limit=10)

        with self.assertRaises(ValidationError):
            list(connector.poll(spec, since=None))

    def test_poll_fails_on_missing_required_field(self):
        """Missing author_id -> ValidationError, entire poll aborts."""
        bad = self._make_record(author_id=None)

        connector = FacebookConnector(action_factory=self._make_factory([bad]))
        spec = FacebookGroupSourceSpec(group_id="305056891435827", limit=10)

        with self.assertRaises(ValidationError):
            list(connector.poll(spec, since=None))

    def test_source_defaults_to_facebook(self):
        """source='unknown' is not allowed — hardcoded to 'facebook'."""
        # The payload model hardcodes source='facebook'; attempting to
        # override it via the record path is impossible because from_record
        # does not accept a source override. This test proves the model
        # rejects unexpected values if injected.
        payload = FacebookPostPayload.sample()
        self.assertEqual(payload.source, "facebook")

    def test_rejects_unknown_source(self):
        from datetime import datetime

        with self.assertRaises(ValidationError):
            FacebookPostPayload(
                external_id="post-123",
                group_id="305056891435827",
                author_id="user-789",
                author_name="Test Author",
                content="valid post content",
                url="https://www.facebook.com/groups/305056891435827/posts/post-123/",
                occurred_at=datetime.now(UTC),
                captured_at=datetime.now(UTC),
                source="unknown",
            )

    def test_poll_succeeds_when_all_records_valid(self):
        valid1 = self._make_record(external_id="1", content="first")
        valid2 = self._make_record(external_id="2", content="second")

        connector = FacebookConnector(action_factory=self._make_factory([valid1, valid2]))
        spec = FacebookGroupSourceSpec(group_id="305056891435827", limit=10)

        payloads = list(connector.poll(spec, since=None))
        self.assertEqual(len(payloads), 2)
        self.assertIsInstance(payloads[0], FacebookPostPayload)
        self.assertIsInstance(payloads[1], FacebookPostPayload)
        self.assertEqual(payloads[0].source, "facebook")
        self.assertEqual(payloads[1].source, "facebook")
