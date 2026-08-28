"""
Facebook Post Payload -- strict Pydantic schema.
Any missing, null, blank, or malformed required field raises ValidationError.
No fabricated defaults. No empty-string substitution.
"""
from datetime import datetime, timezone
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class FacebookPostPayload(BaseModel):
    """
    Normalized payload for a Facebook group post.

    Required (must be present, non-blank, well-formed):
      external_id, group_id, author_id, author_name,
      content, url, occurred_at, captured_at, source
    """
    # Registry key -- required by the Django payload registry
    PAYLOAD_KIND: ClassVar[str] = "facebook_posts"
    SOURCE: ClassVar[str] = "facebook"

    model_config = {"extra": "forbid"}

    external_id: str = Field(..., min_length=1)
    group_id:    str = Field(..., min_length=1)
    author_id:   str = Field(..., min_length=1)
    author_name: str = Field(..., min_length=1)
    content:     str = Field(..., min_length=1)
    url:         str = Field(..., min_length=1)
    occurred_at: datetime
    captured_at: datetime

    source: str = Field(default="facebook", pattern=r"^facebook$")

    title:              Optional[str] = Field(default=None)
    external_url:       Optional[str] = Field(default=None)
    parent_external_id: Optional[str] = Field(default=None)

    kind: str = Field(default="facebook_posts", frozen=True)

    @field_validator(
        "external_id", "group_id", "author_id", "author_name", "content", "url",
        mode="before",
    )
    @classmethod
    def reject_blank(cls, v):
        if v is None:
            raise ValueError("field is required and cannot be None")
        if isinstance(v, str) and not v.strip():
            raise ValueError("field cannot be blank or whitespace-only")
        return v

    @field_validator("url")
    @classmethod
    def validate_facebook_https(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("https://"):
            raise ValueError("url must use HTTPS")
        if "facebook.com" not in v:
            raise ValueError("url must be a facebook.com domain")
        return v

    @model_validator(mode="after")
    def check_url_consistency(self):
        if self.external_id not in self.url:
            raise ValueError("url must contain the post external_id")
        if self.group_id not in self.url:
            raise ValueError("url must contain the group_id")
        return self

    @classmethod
    def from_record(cls, record: Any) -> "FacebookPostPayload":
        def _get(attr, fallback):
            val = getattr(record, attr, None)
            if val is None:
                val = getattr(record, fallback, None)
            return val

        external_id = _get("external_id", "post_id")
        content = _get("content", "text")
        url = _get("url", "permalink")
        occurred_at = _get("occurred_at", "created_at")
        captured_at = getattr(record, "captured_at", None)
        if captured_at is None:
            captured_at = datetime.now(timezone.utc)
        return cls(
            external_id=external_id,
            group_id=getattr(record, "group_id", None),
            author_id=getattr(record, "author_id", None),
            author_name=getattr(record, "author_name", None),
            content=content,
            url=url,
            occurred_at=occurred_at,
            captured_at=captured_at,
            title=getattr(record, "title", None),
            external_url=getattr(record, "external_url", None),
            parent_external_id=getattr(record, "parent_external_id", None),
        )

    @classmethod
    def sample(cls) -> "FacebookPostPayload":
        now = datetime.now(timezone.utc)
        post_id = "1422794306328741"
        group_id = "305056891435827"
        return cls(
            external_id=post_id,
            group_id=group_id,
            author_id="123456789",
            author_name="Acceptance Test User",
            content="Sample post content for registry compliance.",
            url=f"https://www.facebook.com/groups/{group_id}/posts/{post_id}/",
            occurred_at=now,
            captured_at=now,
            source="facebook",
        )