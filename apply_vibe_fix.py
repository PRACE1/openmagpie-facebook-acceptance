"""Apply VIBE BOT's post_to_dict boundary fix."""

from pathlib import Path

# ── 1. Add post_to_dict to post_extractor.py ──────────────────────────
pe_file = Path(r"C:\Users\R5 5600 GT\facebook-camofox-client\src\facebook_camofox_client\domain_extraction\post_extractor.py")
pe_src = pe_file.read_text(encoding="utf-8")

helper = '''

# ── Boundary helper (VIBE BOT) ──
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from typing import Any


def post_to_dict(post: Any) -> dict[str, Any]:
    """Convert ExtractedPost dataclass or mapping into a plain dict."""
    if isinstance(post, Mapping):
        return dict(post)
    if is_dataclass(post) and not isinstance(post, type):
        return asdict(post)
    raise TypeError(f"expected ExtractedPost or mapping, got {type(post).__name__}")

'''

if "def post_to_dict(" not in pe_src:
    pe_file.write_text(pe_src.rstrip() + "\n" + helper, encoding="utf-8")
    print("[OK] Added post_to_dict to post_extractor.py")
else:
    print("[SKIP] post_to_dict already exists")

# ── 2. Clean + patch listen.py ────────────────────────────────────────
listen_file = Path(r"C:\Users\R5 5600 GT\facebook-camofox-client\src\facebook_camofox_client\domain_posts\listen.py")
lines = listen_file.read_text(encoding="utf-8").splitlines()

cleaned = []

for line in lines:
    # Strip all debug lines from earlier attempts
    if "[DEBUG]" in line:
        continue
    
    # Strip misplaced dataclasses import (will add proper import later)
    if line.strip() == "import dataclasses":
        continue
    
    # Strip any direct __dict__ or asdict hacks in the loop
    if "post = post.__dict__" in line or "post = dataclasses.asdict(post)" in line:
        continue
    
    cleaned.append(line)

# Now patch: add import and fix the loop
patched = []
added_import = False
for i, line in enumerate(cleaned):
    # Insert import after the from __future__ line
    if not added_import and line.strip().startswith("from __future__"):
        patched.append(line)
        patched.append("from facebook_camofox_client.domain_extraction.post_extractor import post_to_dict")
        added_import = True
        continue
    
    # Fix _is_degraded: ensure it uses dict .get() (revert any getattr patches)
    if 'getattr(post, "post_id", "")' in line:
        line = line.replace('getattr(post, "post_id", "")', 'post.get("post_id", "")')
    if 'getattr(post, "text", None)' in line:
        line = line.replace('getattr(post, "text", None)', 'post.get("text")')
    
    # Insert post_to_dict conversion inside the for-loop body
    if 'for post in raw_results.get("results", [])' in line:
        indent = len(line) - len(line.lstrip())
        body = " " * (indent + 4)
        patched.append(line)
        patched.append(body + "post = post_to_dict(post)  # boundary: dataclass -> dict")
        continue
    
    patched.append(line)

listen_file.write_text("\n".join(patched) + "\n", encoding="utf-8")
print("[OK] Patched listen.py: import added, loop converts via post_to_dict, _is_degraded uses dict .get()")
print("\nDone. Clear cache and run acceptance test.")