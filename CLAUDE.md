## Session logging to Obsidian

All work in this repo is tracked in an Obsidian vault located at:
`C:\Users\rtske\Obsidian\CommandLog`

Vault structure:
- `Sessions/` — one note per Claude Code working session
- `Archimedes/` — project documentation, dossier index notes
- `Proxmox-Lab/` — lab phase notes and runbooks
- `Handoffs/` — mirrors of repo `docs/handoffs/` documents
- `Inbox/` — unsorted captures

Rules:

1. At the end of any substantive working session (or when I say "wrap up",
   "handoff", or "log this"), run the `/handoff` command workflow: write a
   session note to `Sessions/` in the vault using the standard template
   (BLUF, What was done, Decisions made, Verification status, Next steps,
   Links).
2. Session note filenames: `YYYY-MM-DD-HHmm <short-slug>.md`. Never
   overwrite an existing session note; if one already exists for this
   session, append an `## Update <HHmm>` section instead.
3. When referencing other vault notes, use Obsidian wikilink syntax
   (`[[2026-06-10-1430 splunk dashboard]]`), not relative paths.
4. Frontmatter is mandatory on every note written to the vault: `type`,
   `project`, `date`, `tags`, `status`. This powers Dataview indexes —
   omitting it breaks the dashboards.
5. Notes written to the vault are TLP:CLEAR personal records. Do not copy
   restricted dossier content into the vault; link to the repo path instead.
6. If a session produced a formal handoff in `docs/handoffs/`, mirror it to
   the vault `Handoffs/` folder verbatim.
7. Never delete or bulk-edit existing vault notes without explicit
   confirmation.
