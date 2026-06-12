---
description: Write a session handoff note to the Obsidian vault (and optionally docs/handoffs/)
argument-hint: [short session title, e.g. "thezoo ingestion pivot"]
allowed-tools: Read, Write, Bash(git log:*), Bash(git status:*), Bash(git diff:*)
---

# Session Handoff

Generate a session handoff note and save it to the Obsidian vault.

## Context to gather first

Recent commits this session:
!`git log --oneline -15`

Current working tree state:
!`git status --short`

## Instructions

1. Determine the project name from the repo (e.g. `archimedes`, `proxmox-lab`).
2. Build the filename: `YYYY-MM-DD-HHmm <slug>.md` where the slug comes from
   `$ARGUMENTS` if provided, otherwise a 3-5 word summary of the session.
3. Write the note to the vault sessions folder:
   `C:\Users\rtske\Obsidian\CommandLog\Sessions\`
4. Use EXACTLY this structure:

```markdown
---
type: session
project: <archimedes | proxmox-lab | other>
date: <YYYY-MM-DD>
tags: [session, <project>]
status: <complete | in-progress | blocked>
---

# <Session title>

## BLUF
<2-3 sentences: what was accomplished, current state, and the single most
important thing the next session needs to know.>

## What was done
<Bullet list of concrete actions taken, with commit hashes where relevant.>

## Decisions made
<Any architectural, naming, or convention decisions, with brief rationale.
Write "None" if none.>

## Verification status
<What was tested/verified vs. what is deployed-but-unverified. Reference
explicit verification gates if applicable.>

## Next steps
- [ ] <Ordered, actionable next steps as Obsidian task checkboxes>

## Links
- Repo: <GitHub URL>
- Related notes: <[[wikilinks]] to prior session notes or dossiers if known>
```

5. If this repo has a `docs/handoffs/` directory, ALSO write a copy of the
   note there (same content, same filename) and stage it with git, but do
   NOT commit — leave the commit to me.
6. After writing, print the full path(s) of the file(s) created and a
   one-line confirmation. Do not paraphrase the note back to me in chat.
