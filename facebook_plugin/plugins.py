from django.conf import settings
from sources.registry import register_source

from .connector import FacebookConnector
from .factory import make_action_factory


def register() -> None:
    """Plugin hook for OpenMagpie.

    Usage:
        export OPENMAGPIE_PLUGIN_HOOKS=facebook_plugin.plugins:register
    """
    storage_state = getattr(
        settings,
        "FACEBOOK_STORAGE_STATE",
        r"C:\Users\R5 5600 GT\fb_cookies_playwright.json",
    )
    connector = FacebookConnector(
        action_factory=make_action_factory(
            storage_state_path=storage_state,
            headless=True,
        )
    )
    register_source(connector)