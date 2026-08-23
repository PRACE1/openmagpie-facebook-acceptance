"""Production action_factory for FacebookConnector."""

from __future__ import annotations

import pkgutil
from typing import Any

import facebook_camofox_client
from facebook_camofox_client.domain_camofox.session_manager import CamofoxSessionManager
from facebook_camofox_client.domain_cursors.repository import InMemoryCursorRepository
from facebook_camofox_client.domain_events.emitter import InMemoryEventEmitter
from facebook_camofox_client.domain_posts.listen import PostsListenAction


def _find_normalizer() -> type:
    """Auto-discover PostNormalizer in the facebook-camofox-client package."""
    for mod_name in (
        "facebook_camofox_client.domain_records.normalizer",
        "facebook_camofox_client.domain_extraction.normalizer",
    ):
        try:
            mod = __import__(mod_name, fromlist=["PostNormalizer"])
            if hasattr(mod, "PostNormalizer"):
                return mod.PostNormalizer
        except Exception:
            pass

    for m in pkgutil.walk_packages(
        facebook_camofox_client.__path__, prefix="facebook_camofox_client."
    ):
        try:
            mod = __import__(m.name, fromlist=["PostNormalizer"])
            if hasattr(mod, "PostNormalizer"):
                return mod.PostNormalizer
        except Exception:
            pass

    raise ImportError("PostNormalizer not found in facebook_camofox_client")


class _SessionManagerWithStorageState:
    """Wrap CamofoxSessionManager to inject storage_state_path at acquire time."""

    def __init__(self, session_manager: Any, storage_state_path: str | None) -> None:
        self._sm = session_manager
        self._storage_state_path = storage_state_path

    def acquire(self, account_id: str, proxy_config: Any | None = None, storage_state_path: str | None = None) -> Any:
        return self._sm.acquire(
            account_id,
            proxy_config=proxy_config,
            storage_state_path=storage_state_path or self._storage_state_path,
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._sm, name)


async def _noop_commit(record: Any) -> bool:
    """OpenMagpie handles persistence; client's commit is a no-op."""
    return True


def make_action_factory(
    *,
    storage_state_path: str | None = None,
    headless: bool = True,
) -> Any:
    r"""Return a callable that builds a wired PostsListenAction.

    Usage:
        connector = FacebookConnector(
            action_factory=make_action_factory(
                storage_state_path=r"C:\Users\...\fb_cookies_playwright.json",
            )
        )
    """
    Normalizer = _find_normalizer()

    raw_sm = CamofoxSessionManager()
    session_manager = _SessionManagerWithStorageState(raw_sm, storage_state_path)
    cursor_repo = InMemoryCursorRepository()
    normalizer = Normalizer()
    event_emitter = InMemoryEventEmitter()

    def action_factory() -> PostsListenAction:
        return PostsListenAction(
            session_manager=session_manager,
            cursor_repo=cursor_repo,
            normalizer=normalizer,
            event_emitter=event_emitter,
            commit=_noop_commit,
        )

    return action_factory