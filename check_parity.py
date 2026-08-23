"""Standalone parity check: schema FeedItemData union vs server payloads."""

import ast
import sys
from pathlib import Path
from typing import get_args, get_origin, Literal

sys.path.insert(0, str(Path(r"packages\openmagpie-schema\src")))
sys.path.insert(0, str(Path(r"apps\core")))

from openmagpie_schema.feed_payloads import FeedItemData


def _literal_value(annotation):
    if get_origin(annotation) is Literal:
        args = get_args(annotation)
        if args and isinstance(args[0], str):
            return args[0]
    return None


def _schema_kinds_and_fields():
    union = get_args(FeedItemData)[0]
    result = {}
    for member in get_args(union):
        if member.__name__ == "FeedItemPayload":
            continue
        kind = _literal_value(member.model_fields.get("kind", {}).annotation)
        result[kind] = set(member.model_fields.keys())
    return result


def _server_kinds_and_fields():
    root = Path(r"apps\core\sources\connectors")
    result = {}
    for payloads_file in root.rglob("payloads.py"):
        tree = ast.parse(payloads_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                kind = None
                own_fields = set()
                base_names = {b.id for b in node.bases if isinstance(b, ast.Name)}
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        if item.target.id == "PAYLOAD_KIND" and isinstance