"""Apply VIBE BOT's post_to_dict boundary patch to facebook-camofox-client."""

import re
from pathlib import Path

CLIENT_ROOT = Path(r"C:\Users\R5 5600 GT\facebook-camofox-client\src\facebook_camofox_client")

# ── 1. Add post_to_dict to post_extractor.py ──────────────────────────
pe_file = CLIENT_ROOT / "domain_extraction" / "post_extractor.py"
pe_src = pe_file.read_text()

helper = '''

# ── Boundary helper added by VIBE BOT patch ──
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from typing import Any


def post_to_dict(post: Any) -> dict[str, Any]:
    """Convert a supported extracted-post value into a plain dict."""
    if isinstance(post, Mapping):
        return dict(post)
    if is_dataclass(post):
        return asdict(post)
    model_dump = getattr(post, "model_dump", None)
    if callable(model_dump):
        value = model_dump()
        if not isinstance(value, dict):
            raise TypeError(f"model_dump() must return dict, got {type(value)!r}")
        return value
    raise TypeError(f"unsupported extracted post type: {type(post).__name__}")

'''

if "def post_to_dict(" not in pe_src:
    pe_file.write_text(pe_src.rstrip() + "\n" + helper)
    print(f"[OK] Added post_to_dict to {pe_file}")
else:
    print(f"[SKIP] post_to_dict already exists in {pe_file}")

# ── 2. Patch domain_posts/listen.py ───────────────────────────────────
listen_file = CLIENT_ROOT / "domain_posts" / "listen.py"
listen_src = listen_file.read_text()

# Add import
if "from facebook_camofox_client.domain_extraction.post_extractor import post_to_dict" not in listen_src:
    # Find a good insertion point (after other facebook_camofox_client imports)
    listen_src = listen_src.replace(
        "from facebook_camofox_client.domain_extraction.post_extractor import",
        "from facebook_camofox_client.domain_extraction.post_extractor import post_to_dict,",
    )
    print("[OK] Added post_to_dict import to listen.py")
else:
    print("[SKIP] Import already present in listen.py")

# Replace the results loop: convert BEFORE _is_degraded
# This regex targets the pattern:
#   for post in raw_results.get("results", []):
#       if _is_degraded(post):
old_pattern = r'(for post in raw_results\.get\("results", \[\]\):)(\s+if _is_degraded\(post\):)'
new_replacement = r'\1\n    post_dict = post_to_dict(post)\n    if _is_degraded(post_dict):'

if "post_dict = post_to_dict(post)" not in listen_src:
    listen_src_new, count = re.subn(old_pattern, new_replacement, listen_src)
    if count:
        listen_file.write_text(listen_src_new)
        print(f"[OK] Patched {count} loop(s) in listen.py to convert before _is_degraded")
    else:
        print("[WARN] Could not find the exact loop pattern in listen.py")
        print("       Manual edit may be required.")
else:
    print("[SKIP] Loop already patched in listen.py")

# ── 3. Patch domain_groups/search.py (same risk) ──────────────────────
search_file = CLIENT_ROOT / "domain_groups" / "search.py"
if search_file.exists():
    search_src = search_file.read_text()
    if "post_to_dict" not in search_src:
        # Add import
        search_src = search_src.replace(
            "from facebook_camofox_client.domain_extraction.post_extractor import",
            "from facebook_camo