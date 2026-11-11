"""Map tool and method names onto the canonical names in vocab/vocabulary.json."""

import json
import re

from common import ROOT

VOCAB = ROOT / "vocab" / "vocabulary.json"
# A trailing version: "Seurat v4", "Monocle 3", "CellMarker 2.0", "CellPhoneDB v3".
VERSION = re.compile(r"^(?P<base>.*?\S)\s+v?(?P<version>\d+(?:\.\d+)*)$", re.IGNORECASE)


def key(name: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9+]+", " ", name.lower()).split())


class Vocabulary:
    def __init__(self):
        data = json.loads(VOCAB.read_text(encoding="utf-8"))
        self.tools = {}
        self.methods = {}
        for kind, table in (("tools", self.tools), ("methods", self.methods)):
            for entry in data[kind]:
                for alias in [entry["name"], *entry.get("aliases", [])]:
                    table[key(alias)] = entry
        self.unlisted = {"tools": set(), "methods": set()}

    def lookup(self, name: str, kind: str):
        """Return (canonical entry or None, version) without recording misses."""
        table = self.tools if kind == "tools" else self.methods
        entry = table.get(key(name))
        if entry is not None:
            return entry, ""
        m = VERSION.match(name.strip())
        if m and key(m["base"]) in table:
            return table[key(m["base"])], m["version"]
        return None, ""

    def canon(self, name: str, kind: str):
        """Return (canonical entry, version). Unknown names get a stub entry and are recorded."""
        entry, version = self.lookup(name, kind)
        if entry is None:
            self.unlisted[kind].add(name)
            entry = {"name": name, "unlisted": True}
        return entry, version
