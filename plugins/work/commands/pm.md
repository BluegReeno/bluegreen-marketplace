---
description: Work — the sprint board (`tasks`) or the status of one project (`plan`); anything else is a plain sentence
argument-hint: "tasks [workspace] [--mine] [--all] | plan <project>"
---

Run the `pm` skill of the `work` plugin with the argument `$ARGUMENTS`. The skill body is not
pre-loaded by this command: load it first (Skill tool, `work:pm`), then follow its `tasks` or
`plan` section. With no argument, ask which of the two is wanted.
