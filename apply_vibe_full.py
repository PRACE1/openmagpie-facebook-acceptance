"""Apply VIBE BOT's full patch: restore commit boundary + reorder save/emit."""

from pathlib import Path

listen_file = Path(r"C:\Users\R5 5600 GT\facebook-camofox-client\src\facebook_camofox_client\domain_posts\listen.py")
text = listen_file.read_text(encoding="utf-8")
lines = text.splitlines()

# ── 1. Add imports after from __future__ ──────────────────────────────
import_block = '''from collections.abc import Awaitable, Callable
from facebook_camofox_client.domain_records.models import NormalizedPostRecord

CommitCallback = Callable[[NormalizedPostRecord], Awaitable[bool]]

'''

if "CommitCallback" not in text:
    # Insert after the first non-future import line, or after __future__
    for i, line in enumerate(lines):
        if line.strip().startswith("from __future__"):
            lines.insert(i + 1, "from facebook_camofox_client.domain_extraction.post_extractor import post_to_dict")
            lines.insert(i + 2, import_block.strip())
            break

# Re-read as single text for easier regex
text = "\n".join(lines)

# ── 2. Patch __init__ to accept commit ────────────────────────────────
old_init = '''    def __init__(self, session_manager, cursor_repo, normalizer, event_emitter):
        self.session_manager = session_manager
        self.cursor_repo = cursor_repo
        self.normalizer = normalizer
        self.event_emitter = event_emitter'''

new_init = '''    def __init__(self, session_manager, cursor_repo, normalizer,
                 event_emitter, commit: CommitCallback):
        self.session_manager = session_manager
        self.cursor_repo = cursor_repo
        self.normalizer = normalizer
        self.event_emitter = event_emitter
        self.commit = commit'''

text = text.replace(old_init, new_init)

# ── 3. Replace post.__dict__ with post_to_dict(post) ──────────────────
text = text.replace("post = post.__dict__", "post = post_to_dict(post)")

# ── 4. Reorder the loop: normalize all → commit all → save cursor → emit
# Find and replace the entire for-loop block and what follows it.
# We target the pattern from "for post in raw_results..." through the emit/cursor save.

old_loop_pattern = '''        for post in raw_results.get("results", []):
            post = post_to_dict(post)
            if _is_degraded(post):
                continue
            normalized = self.normalizer.normalize(post, envelope.account_id, envelope.action_type)
            new_posts.append(normalized)
            await self.commit(normalized)
            await self.event_emitter.emit("posts.new", normalized)'''

new_loop_pattern = '''        # Phase 1: normalize all extracted posts
        for post in raw_results.get("results", []):
            post = post_to_dict(post)
            if _is_degraded(post):
                continue
            normalized = self.normalizer.normalize(post, envelope.account_id, envelope.action_type)
            new_posts.append(normalized)

        # Phase 2: commit every record durably before saving cursor or emitting
        for record in new_posts:
            try:
                ok = await self.commit(record)
            except Exception as exc:
                raise CommitFailed(f"commit failed for {record.external_id}: {exc}") from exc
            if not ok:
                raise CommitFailed(f"commit returned False for {record.external_id}")

        # Phase 3: cursor is now safe to advance
        cursor_advanced = False
        if new_posts:
            last_cursor = new_posts[-1].cursor
            if last_cursor:
                self.cursor_repo.save(envelope.account_id, envelope.input.get("group_id"), last_cursor)
                cursor_advanced = True

        # Phase 4: emit events only after cursor is durable
        for record in new_posts:
            await self.event_emitter.emit("posts.new", record)'''

# Handle case where the old loop might not have post_to_dict yet (restored file)
if old_loop_pattern not in text:
    # Try without post_to_dict line (restored git version)
    alt_old = '''        for post in raw_results.get("results", []):
            if _is_degraded(post):
                continue
            normalized = self.normalizer.normalize(post, envelope.account_id, envelope.action_type)
            new_posts.append(normalized)
            await self.commit(normalized)
            await self.event_emitter.emit("posts.new", normalized)'''
    if alt_old in text:
        text = text.replace(alt_old, new_loop_pattern)
    else:
        print("[WARN] Could not find exact loop pattern. Manual edit required.")
else:
    text = text.replace(old_loop_pattern, new_loop_pattern)

# ── 5. Add CommitFailed exception if missing ──────────────────────────
if "class CommitFailed" not in text:
    # Insert before PostsListenAction class
    text = text.replace(
        "class PostsListenAction:",
        "class CommitFailed(RuntimeError):\n    \"\"\"Raised when a record commit fails before cursor is saved.\"\"\"\n\n\nclass PostsListenAction:"
    )

listen_file.write_text(text, encoding="utf-8")
print("[OK] Patched listen.py:")
print("  - CommitCallback restored to __init__")
print("  - post_to_dict replaces __dict__")
print("  - Commit/all-then-cursor-then-emit ordering applied")
print("  - CommitFailed exception added")