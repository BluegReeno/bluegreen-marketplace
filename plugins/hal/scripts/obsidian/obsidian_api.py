"""Obsidian vault client — dual-mode: REST API or direct filesystem access.

AUTO-DETECTION:
  1. Try REST API at config's api_url (works when Obsidian is open + Local REST API plugin)
  2. Fall back to direct filesystem access via vault_path in config.json
  3. vault_path can be overridden by OBSIDIAN_VAULT_PATH env var

The public interface is identical regardless of backend:
  - read_note(path)   → dict with frontmatter, content, path, tags
  - read_raw(path)    → raw markdown string
  - create_note(path, content, overwrite=False)
  - append_body(path, content)
  - update_field(path, field, value)
  - list_directory(folder)   → list of filenames
  - search_simple(query)     → list of matches
  - search_dql(dql)          → list of results (API-only, graceful fallback)
  - note_exists(path)        → bool
"""

import json
import os
import re
import sys
import unicodedata
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    """Load config from config.json. Env vars override if set."""
    cfg = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
    if os.environ.get("OBSIDIAN_API_KEY"):
        cfg["api_key"] = os.environ["OBSIDIAN_API_KEY"]
    if os.environ.get("OBSIDIAN_API_URL"):
        cfg["api_url"] = os.environ["OBSIDIAN_API_URL"]
    if os.environ.get("OBSIDIAN_VAULT_PATH"):
        cfg["vault_path"] = os.environ["OBSIDIAN_VAULT_PATH"]
    return cfg


# ---------------------------------------------------------------------------
# REST API backend
# ---------------------------------------------------------------------------

class _RestBackend:
    """HTTP backend using Obsidian Local REST API."""

    def __init__(self, base_url: str, api_key: str):
        import requests
        import urllib3
        import urllib.parse
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self._requests = requests
        self._urllib_parse = urllib.parse
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers["Authorization"] = f"Bearer {api_key}"

    def _url(self, path: str) -> str:
        segments = path.split("/")
        encoded = "/".join(self._urllib_parse.quote(s, safe="") for s in segments)
        return f"{self.base_url}/vault/{encoded}"

    def read_note(self, path: str) -> dict:
        r = self.session.get(
            self._url(path),
            headers={"Accept": "application/vnd.olrapi.note+json"},
        )
        r.raise_for_status()
        return r.json()

    def read_raw(self, path: str) -> str:
        r = self.session.get(self._url(path))
        r.raise_for_status()
        return r.text

    def create_note(self, path: str, content: str, overwrite: bool = False) -> None:
        if not overwrite and self.note_exists(path):
            raise FileExistsError(f"Note already exists: {path}")
        r = self.session.put(
            self._url(path),
            headers={"Content-Type": "text/markdown"},
            data=content.encode("utf-8"),
        )
        r.raise_for_status()

    def append_body(self, path: str, content: str) -> None:
        r = self.session.post(
            self._url(path),
            headers={"Content-Type": "text/markdown"},
            data=content.encode("utf-8"),
        )
        r.raise_for_status()

    def delete_note(self, path: str) -> None:
        r = self.session.delete(self._url(path))
        r.raise_for_status()

    def update_field(self, path: str, field: str, value) -> None:
        r = self.session.patch(
            self._url(path),
            headers={
                "Content-Type": "application/json",
                "Operation": "replace",
                "Target-Type": "frontmatter",
                "Target": field,
            },
            data=json.dumps(value).encode("utf-8"),
        )
        r.raise_for_status()

    def list_directory(self, folder: str) -> list:
        url = self._url(folder)
        if not url.endswith("/"):
            url += "/"
        r = self.session.get(url)
        r.raise_for_status()
        data = r.json()
        return data.get("files", data) if isinstance(data, dict) else data

    def search_simple(self, query: str, context_length: int = 200) -> list:
        r = self.session.post(
            f"{self.base_url}/search/simple/",
            params={"query": query, "contextLength": context_length},
        )
        r.raise_for_status()
        return r.json()

    def search_dql(self, dql: str) -> list:
        r = self.session.post(
            f"{self.base_url}/search/",
            headers={"Content-Type": "application/vnd.olrapi.dataview.dql+txt"},
            data=dql.encode("utf-8"),
        )
        r.raise_for_status()
        return r.json()

    def note_exists(self, path: str) -> bool:
        r = self.session.get(self._url(path))
        return r.status_code == 200

    def status(self) -> dict:
        import requests
        r = requests.get(f"{self.base_url}/", verify=False, timeout=3)
        r.raise_for_status()
        return r.json()


# ---------------------------------------------------------------------------
# Filesystem backend
# ---------------------------------------------------------------------------

class _FileBackend:
    """Direct filesystem backend — reads/writes Markdown files."""

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        if not self.vault.is_dir():
            raise FileNotFoundError(f"Vault not found: {vault_path}")

    def _resolve(self, path: str) -> Path:
        """Resolve vault-relative path to absolute, with NFC normalization."""
        normalized = unicodedata.normalize("NFC", path)
        return self.vault / normalized

    # --- Frontmatter parsing (no PyYAML — manual, safe) ---

    @staticmethod
    def _split_frontmatter(text: str) -> tuple:
        """Split markdown into (frontmatter_str, body_str).

        Returns ("", full_text) if no frontmatter block found.
        """
        if not text.startswith("---"):
            return "", text
        # Find closing ---
        end = text.find("\n---", 3)
        if end == -1:
            return "", text
        fm_str = text[4:end]  # skip opening "---\n"
        body = text[end + 4:]  # skip closing "\n---"
        if body.startswith("\n"):
            body = body[1:]
        return fm_str, body

    @staticmethod
    def _parse_frontmatter(fm_str: str) -> dict:
        """Minimal YAML parser for Obsidian frontmatter.

        Handles: strings, numbers, booleans, lists (inline and indented),
        wikilinks in double quotes. Does NOT handle nested objects.
        """
        if not fm_str.strip():
            return {}

        result = {}
        lines = fm_str.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]

            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith("#"):
                i += 1
                continue

            # Key: value line
            m = re.match(r'^([A-Za-z_][\w_-]*)\s*:\s*(.*)', line)
            if not m:
                i += 1
                continue

            key = m.group(1)
            raw_value = m.group(2).strip()

            # Check for indented list on next lines
            if raw_value == "" or raw_value == "|":
                # Could be a list or multiline
                list_items = []
                j = i + 1
                while j < len(lines) and lines[j].startswith("  "):
                    item_line = lines[j].strip()
                    if item_line.startswith("- "):
                        list_items.append(_FileBackend._parse_scalar(item_line[2:].strip()))
                    j += 1
                if list_items:
                    result[key] = list_items
                    i = j
                    continue
                elif raw_value == "":
                    result[key] = None
                    i += 1
                    continue

            # Inline list: [a, b, c]
            if raw_value.startswith("[") and raw_value.endswith("]"):
                inner = raw_value[1:-1].strip()
                if not inner:
                    result[key] = []
                else:
                    items = _FileBackend._split_inline_list(inner)
                    result[key] = [_FileBackend._parse_scalar(it.strip()) for it in items]
                i += 1
                continue

            # Scalar
            result[key] = _FileBackend._parse_scalar(raw_value)
            i += 1

        return result

    @staticmethod
    def _split_inline_list(s: str) -> list:
        """Split 'a, "b, c", d' respecting quotes."""
        items = []
        current = ""
        in_quotes = False
        quote_char = None
        for ch in s:
            if ch in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = ch
                current += ch
            elif ch == quote_char and in_quotes:
                in_quotes = False
                current += ch
                quote_char = None
            elif ch == "," and not in_quotes:
                items.append(current.strip())
                current = ""
            else:
                current += ch
        if current.strip():
            items.append(current.strip())
        return items

    @staticmethod
    def _parse_scalar(s: str):
        """Parse a YAML scalar value."""
        if not s:
            return None
        # Remove surrounding quotes
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1].replace('\\"', '"').replace("\\'", "'")
        # Booleans
        if s.lower() == "true":
            return True
        if s.lower() == "false":
            return False
        if s.lower() == "null":
            return None
        # Numbers
        try:
            if "." in s:
                return float(s)
            return int(s)
        except ValueError:
            pass
        return s

    @staticmethod
    def _serialize_frontmatter(fm: dict) -> str:
        """Serialize dict to YAML frontmatter (no PyYAML)."""
        lines = []
        for key, value in fm.items():
            formatted = _FileBackend._yaml_value(value)
            if formatted.startswith("\n"):
                lines.append(f"{key}:{formatted}")
            else:
                lines.append(f"{key}: {formatted}")
        return "\n".join(lines)

    @staticmethod
    def _yaml_value(value) -> str:
        """Format a Python value as safe YAML."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, list):
            if not value:
                return "[]"
            items = [f"  - {_FileBackend._yaml_value(v)}" for v in value]
            return "\n" + "\n".join(items)
        s = str(value)
        s = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{s}"'

    # --- Extract tags from content ---

    @staticmethod
    def _extract_tags(text: str) -> list:
        """Extract #tags from markdown body (not frontmatter)."""
        return re.findall(r'(?<!\w)#([A-Za-z_][\w/-]*)', text)

    # --- Public interface ---

    def read_note(self, path: str) -> dict:
        fp = self._resolve(path)
        if not fp.exists():
            raise FileNotFoundError(f"Note not found: {path}")
        text = fp.read_text(encoding="utf-8")
        fm_str, body = self._split_frontmatter(text)
        fm = self._parse_frontmatter(fm_str)
        stat = fp.stat()
        return {
            "frontmatter": fm,
            "content": body,
            "path": path,
            "tags": fm.get("tags", []) or self._extract_tags(body),
            "stat": {
                "ctime": int(stat.st_ctime * 1000),
                "mtime": int(stat.st_mtime * 1000),
                "size": stat.st_size,
            },
        }

    def read_raw(self, path: str) -> str:
        fp = self._resolve(path)
        if not fp.exists():
            raise FileNotFoundError(f"Note not found: {path}")
        return fp.read_text(encoding="utf-8")

    def create_note(self, path: str, content: str, overwrite: bool = False) -> None:
        fp = self._resolve(path)
        if not overwrite and fp.exists():
            raise FileExistsError(f"Note already exists: {path}")
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")

    def append_body(self, path: str, content: str) -> None:
        fp = self._resolve(path)
        if not fp.exists():
            raise FileNotFoundError(f"Note not found: {path}")
        with open(fp, "a", encoding="utf-8") as f:
            f.write(content)

    def delete_note(self, path: str) -> None:
        fp = self._resolve(path)
        if not fp.exists():
            raise FileNotFoundError(f"Note not found: {path}")
        fp.unlink()

    def update_field(self, path: str, field: str, value) -> None:
        fp = self._resolve(path)
        if not fp.exists():
            raise FileNotFoundError(f"Note not found: {path}")

        text = fp.read_text(encoding="utf-8")
        fm_str, body = self._split_frontmatter(text)
        fm = self._parse_frontmatter(fm_str)

        # Update the field
        fm[field] = value

        # Rebuild the file
        new_fm = self._serialize_frontmatter(fm)
        new_content = f"---\n{new_fm}\n---\n{body}"
        fp.write_text(new_content, encoding="utf-8")

    def list_directory(self, folder: str) -> list:
        dp = self._resolve(folder)
        if not dp.is_dir():
            raise FileNotFoundError(f"Folder not found: {folder}")
        return sorted([f.name for f in dp.iterdir() if f.suffix == ".md"])

    def search_simple(self, query: str, context_length: int = 200) -> list:
        """Full-text search across all .md files in the vault."""
        query_lower = query.lower()
        results = []
        for fp in self.vault.rglob("*.md"):
            # Skip hidden folders (.obsidian, .trash, etc.)
            parts = fp.relative_to(self.vault).parts
            if any(p.startswith(".") for p in parts):
                continue

            try:
                text = fp.read_text(encoding="utf-8")
            except Exception:
                continue

            if query_lower in text.lower():
                rel = str(fp.relative_to(self.vault))
                # Find match positions for context
                matches = []
                idx = 0
                text_lower = text.lower()
                while True:
                    pos = text_lower.find(query_lower, idx)
                    if pos == -1:
                        break
                    start = max(0, pos - context_length // 2)
                    end = min(len(text), pos + len(query) + context_length // 2)
                    matches.append({
                        "context": text[start:end],
                        "offset": pos,
                    })
                    idx = pos + 1
                    if len(matches) >= 5:
                        break

                results.append({
                    "filename": rel,
                    "score": len(matches),
                    "matches": matches,
                })

        # Sort by number of matches descending
        results.sort(key=lambda r: r["score"], reverse=True)
        return results

    def search_dql(self, dql: str) -> list:
        """Parse a subset of DQL (TABLE ... FROM ... WHERE ... SORT).

        Supports basic TABLE queries that are common in CRM usage.
        Falls back gracefully with a helpful error for unsupported syntax.
        """
        # Parse: TABLE field1, field2 FROM "folder" WHERE condition SORT field DIR
        m = re.match(
            r'TABLE\s+(.*?)\s+FROM\s+"([^"]+)"'
            r'(?:\s+WHERE\s+(.*?))?'
            r'(?:\s+SORT\s+([\w_]+)\s*(ASC|DESC)?)?'
            r'\s*$',
            dql.strip(),
            re.IGNORECASE,
        )
        if not m:
            raise ValueError(
                f"DQL not supported in filesystem mode. "
                f"Use search_simple() or list_directory() + read_note() instead. "
                f"DQL requires Obsidian REST API."
            )

        columns = [c.strip() for c in m.group(1).split(",")]
        folder = m.group(2)
        where_clause = m.group(3)
        sort_field = m.group(4)
        sort_dir = (m.group(5) or "ASC").upper()

        # List and read notes
        dp = self._resolve(folder)
        if not dp.is_dir():
            raise FileNotFoundError(f"Folder not found: {folder}")

        rows = []
        for fp in sorted(dp.glob("*.md")):
            try:
                text = fp.read_text(encoding="utf-8")
            except Exception:
                continue

            fm_str, _ = self._split_frontmatter(text)
            fm = self._parse_frontmatter(fm_str)
            name = fp.stem

            # Apply WHERE filter
            if where_clause and not self._eval_where(fm, where_clause):
                continue

            row = {"file": {"name": name, "path": str(fp.relative_to(self.vault))}}
            for col in columns:
                row[col] = fm.get(col)
            rows.append(row)

        # Sort
        if sort_field:
            reverse = sort_dir == "DESC"
            rows.sort(
                key=lambda r: (r.get(sort_field) is None, str(r.get(sort_field, ""))),
                reverse=reverse,
            )

        return rows

    @staticmethod
    def _eval_where(fm: dict, clause: str) -> bool:
        """Evaluate a simple WHERE clause against frontmatter.

        Supports:
          - field != "value"
          - field = "value"
          - contains(field, "value")
          - AND combinations
        """
        # Split on AND (case-insensitive)
        parts = re.split(r'\s+AND\s+', clause, flags=re.IGNORECASE)
        for part in parts:
            part = part.strip()
            if not _FileBackend._eval_condition(fm, part):
                return False
        return True

    @staticmethod
    def _eval_condition(fm: dict, cond: str) -> bool:
        """Evaluate a single condition."""
        # Normalize: remove stray backslashes from shell escaping (e.g. \!= -> !=)
        cond = cond.replace("\\!", "!")

        # contains(field, "value")
        m = re.match(r'contains\(\s*(\w+)\s*,\s*"([^"]+)"\s*\)', cond)
        if m:
            field_val = fm.get(m.group(1))
            target = m.group(2)
            if isinstance(field_val, list):
                return target in field_val
            if isinstance(field_val, str):
                return target in field_val
            return False

        # field != "value"
        m = re.match(r'(\w+)\s*!=\s*"([^"]*)"', cond)
        if m:
            return str(fm.get(m.group(1), "")) != m.group(2)

        # field = "value"
        m = re.match(r'(\w+)\s*=\s*"([^"]*)"', cond)
        if m:
            return str(fm.get(m.group(1), "")) == m.group(2)

        # Unknown condition — pass through (be permissive)
        return True

    def note_exists(self, path: str) -> bool:
        return self._resolve(path).exists()

    def status(self) -> dict:
        return {
            "status": "ok",
            "backend": "filesystem",
            "vault_path": str(self.vault),
            "note_count": sum(1 for _ in self.vault.rglob("*.md")),
        }


# ---------------------------------------------------------------------------
# Unified ObsidianAPI — auto-detects backend
# ---------------------------------------------------------------------------

class ObsidianAPI:
    """Unified Obsidian client. Tries REST API first, falls back to filesystem."""

    def __init__(self, config: dict | None = None, force_backend: str | None = None):
        """
        Args:
            config: Optional config dict. Loaded from config.json if None.
            force_backend: "api" or "file" to skip auto-detection.
        """
        cfg = config or load_config()
        self._backend = None
        self.backend_name = None

        if force_backend == "file":
            self._init_file(cfg)
        elif force_backend == "api":
            self._init_api(cfg)
        else:
            # Auto-detect: try API first, fallback to filesystem
            if cfg.get("api_url") and cfg.get("api_key"):
                try:
                    self._init_api(cfg)
                    # Quick connectivity check
                    self._backend.status()
                except Exception as e:
                    print(f"[obsidian_api] REST API unavailable ({e!r}), falling back to filesystem",
                          file=sys.stderr)
                    self._backend = None

            if self._backend is None:
                self._init_file(cfg)

    def _init_api(self, cfg: dict):
        self._backend = _RestBackend(cfg["api_url"], cfg["api_key"])
        self.backend_name = "api"

    def _init_file(self, cfg: dict):
        vault_path = cfg.get("vault_path")
        if not vault_path:
            raise RuntimeError(
                "No vault_path in config.json and REST API unreachable. "
                "Set vault_path in config.json or OBSIDIAN_VAULT_PATH env var."
            )
        self._backend = _FileBackend(vault_path)
        self.backend_name = "file"

    # --- Proxy all methods to the active backend ---

    def read_note(self, path: str) -> dict:
        return self._backend.read_note(path)

    def read_raw(self, path: str) -> str:
        return self._backend.read_raw(path)

    def create_note(self, path: str, content: str, overwrite: bool = False) -> None:
        return self._backend.create_note(path, content, overwrite)

    def append_body(self, path: str, content: str) -> None:
        return self._backend.append_body(path, content)

    def delete_note(self, path: str) -> None:
        return self._backend.delete_note(path)

    def update_field(self, path: str, field: str, value) -> None:
        return self._backend.update_field(path, field, value)

    def list_directory(self, folder: str) -> list:
        return self._backend.list_directory(folder)

    def search_simple(self, query: str, context_length: int = 200) -> list:
        return self._backend.search_simple(query, context_length)

    def search_dql(self, dql: str) -> list:
        return self._backend.search_dql(dql)

    def note_exists(self, path: str) -> bool:
        return self._backend.note_exists(path)

    def status(self) -> dict:
        return self._backend.status()


if __name__ == "__main__":
    api = ObsidianAPI()
    print(f"Backend: {api.backend_name}")
    s = api.status()
    for k, v in s.items():
        print(f"  {k}: {v}")
