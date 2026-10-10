"""Shared helpers for the skill-contract tests: frontmatter parsing and the hal-mcp tool list.

Frontmatter is parsed by hand (no PyYAML at CI time).

HAL_TOOLS is the tool list of the target `hal-mcp` (supabase/functions/hal-mcp/index.ts in the hal
repo, 29 registerTool calls, read 2026-10-09). A skill that names a tool outside it is calling
something that does not exist; when hal adds, renames or removes a tool, this list changes in the
same commit as the skills.
"""
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent
PREFIX = "mcp__plugin_hal_hal-mcp__"

HAL_TOOLS = frozenset("""
list_projects create_project update_project_stage update_project
create_company list_companies update_company
create_contact list_contacts update_contact
log_interaction list_interactions update_interaction
create_sprint list_sprints update_sprint transition_sprint assign_task_to_sprint
create_task list_tasks update_task_status update_task
save_document list_documents get_document get_document_link
kb_index kb_search whoami
""".split())

# A hal tool is spelled verb_noun; these verbs are the ones the 29 names start with.
_TOOL_LIKE = re.compile(
    r"\b(?:list|create|update|get|save|log|assign|transition)_[a-z_]+\b|\bkb_[a-z_]+\b|\bwhoami\b"
)
# Names that look like a tool and are not one (a CLI flag, a column, a script verb).
_NOT_TOOLS = frozenset({
    "log_cr",
    # Tools of other connectors (Granola, Google Calendar) that gtm:call calls.
    "list_calendars", "list_events", "list_meetings", "get_meetings", "get_meeting_transcript",
    "get_account_info",
})


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def frontmatter(path: pathlib.Path) -> dict:
    """The `key: value` pairs of the YAML block — folded `>` scalars joined on one line."""
    m = re.match(r"^---\n(.*?)\n---\n", read(path), re.S)
    assert m, f"{path} has no frontmatter"
    fields, key = {}, None
    for line in m.group(1).splitlines():
        if line.startswith(" ") and key:
            fields[key] = (fields[key] + " " + line.strip()).strip()
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        fields[key] = value.strip().lstrip(">").strip()
    return fields


def allowed_tools(path: pathlib.Path) -> list:
    # `Bash(uv *)` holds a space: tokens are either `Name(...)` or a bare name.
    return re.findall(r"\S+\([^)]*\)|\S+", frontmatter(path)["allowed-tools"].strip('"'))


def hal_tools_allowed(path: pathlib.Path) -> set:
    return {t[len(PREFIX):] for t in allowed_tools(path) if t.startswith(PREFIX)}


def hal_tools_mentioned(path: pathlib.Path) -> set:
    body = re.sub(r"^---\n.*?\n---\n", "", read(path), count=1, flags=re.S)
    return {t for t in _TOOL_LIKE.findall(body) if t not in _NOT_TOOLS}


def flat(text: str) -> str:
    """Whitespace collapsed, so an assertion survives a re-wrapped paragraph."""
    return " ".join(text.split())
