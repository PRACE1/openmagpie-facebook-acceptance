from datetime import datetime, timezone
from typing import ClassVar

from sources.payloads import SourcePayload


class FacebookPostPayload(SourcePayload):
    """A Facebook group post, mapped from NormalizedPostRecord."""

    PAYLOAD_KIND: ClassVar[str] = "facebook_post"

    group_id: str = ""
    author_name: str = ""
    author_id: str = ""

    model_config = {"frozen": True}

    @classmethod
    def sample(cls, variant: int = 0) -> "FacebookPostPayload":
        n = variant + 1
        return cls(
            external_id=f"fb_post_{n}",
            kind=cls.PAYLOAD_KIND,
            occurred_at=datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc),
            source="facebook_posts",
            title=f"Example Facebook post {n}",
            content="Example post content from a Facebook group.",
            url=f"https://web.facebook.com/groups/305056891435827/posts/{n}",
            external_url="",
            group_id="305056891435827",
            author_name="Example Author",
            author_id="123456789",
        )

    @classmethod
    def from_record(cls, record) -> "FacebookPostPayload":
        """Map a NormalizedPostRecord to a typed payload.

        Rejects records with invented/missing fields by raising if the
        caller passed an invalid record. The connector's _is_valid gate
        should have already filtered these.
        """
        permalink = getattr(record, "permalink", None) or getattr(record, "url", None)

        if not record.external_id:
            raise ValueError("external_id is required")
        if not permalink:
            raise ValueError("permalink is required")
        if not record.occurred_at:
            raise ValueError("occurred_at is required")

        return cls(
            external_id=record.external_id,
            kind=cls.PAYLOAD_KIND,
            occurred_at=record.occurred_at,
            source="facebook_posts",
            title="",
            content=record.content,
            url=permalink,
            external_url="",
            group_id=record.group_id,
            author_name=getattr(record, "author_name", "") or "",
            author_id=getattr(record, "author_id", "") or "",
        )