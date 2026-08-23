import pytest
from datetime import datetime, timezone

from facebook_plugin.payloads import FacebookPostPayload
from facebook_plugin.connector import FacebookConnector


class FakeRecord:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_payload_sample_returns_distinct_variants():
    a = FacebookPostPayload.sample(variant=0)
    b = FacebookPostPayload.sample(variant=1)
    assert a.external_id != b.external_id
    assert a.url != b.url
    assert a.kind == "facebook_post"
    assert a.source == "facebook_posts"


def test_payload_from_record_maps_fields():
    record = FakeRecord(
        external_id="123",
        permalink="https://web.facebook.com/groups/305/posts/123/",
        occurred_at=datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc),
        group_id="305",
        content="hello world",
        author_name="Alice",
        author_id="999",
    )
    payload = FacebookPostPayload.from_record(record)
    assert payload.external_id == "123"
    assert payload.url == "https://web.facebook.com/groups/305/posts/123/"
    assert payload.content == "hello world"
    assert payload.group_id == "305"
    assert payload.author_name == "Alice"


def test_payload_from_record_rejects_missing_external_id():
    record = FakeRecord(
        external_id="",
        permalink="https://example.com",
        occurred_at=datetime.now(timezone.utc),
        group_id="305",
        content="x",
    )
    with pytest.raises(ValueError, match="external_id"):
        FacebookPostPayload.from_record(record)


def test_connector_poll_yields_typed_payloads():
    class FakeAction:
        def execute(self, spec):
            class Result:
                new_posts = [
                    FakeRecord(
                        external_id="1",
                        permalink="https://fb.com/g/1/posts/1",
                        occurred_at=datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc),
                        group_id="1",
                        content="post one",
                        author_name="A",
                        author_id="100",
                    ),
                    FakeRecord(
                        external_id="2",
                        permalink="https://fb.com/g/1/posts/2",
                        occurred_at=datetime(2026, 8, 21, 12, 1, 0, tzinfo=timezone.utc),
                        group_id="1",
                        content="post two",
                        author_name="B",
                        author_id="200",
                    ),
                ]
            return Result()

    conn = FacebookConnector(action_factory=lambda: FakeAction())
    payloads = list(conn.poll(spec=None, since=None))
    assert len(payloads) == 2
    assert all(isinstance(p, FacebookPostPayload) for p in payloads)
    assert payloads[0].external_id == "1"
    assert payloads[1].external_id == "2"


def test_connector_poll_skips_invalid_records():
    class FakeAction:
        def execute(self, spec):
            class Result:
                new_posts = [
                    FakeRecord(
                        external_id="1",
                        permalink="https://fb.com/g/1/posts/1",
                        occurred_at=datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc),
                        group_id="1",
                        content="valid",
                    ),
                    FakeRecord(
                        external_id="",
                        permalink="",
                        occurred_at=None,
                        group_id="",
                        content="invalid",
                    ),
                ]
            return Result()

    conn = FacebookConnector(action_factory=lambda: FakeAction())
    payloads = list(conn.poll(spec=None, since=None))
    assert len(payloads) == 1
    assert payloads[0].external_id == "1"


def test_connector_poll_requires_factory():
    conn = FacebookConnector()
    with pytest.raises(RuntimeError, match="action_factory"):
        list(conn.poll(spec=None, since=None))