# Claude Conversations

This folder is for local Claude review/transcript artifacts.

What lives here:
- `*.md` transcript files you can read while the conversation is happening
- hidden sidecar files like `.working-tree-review.meta.json` that the wrapper uses internally

Git behavior:
- transcript and state files in this folder are ignored by Git
- this README stays tracked so the folder exists and its purpose is documented

About the hidden JSON sidecar:
- you do not need to read it
- it is mainly wrapper bookkeeping
- it stores the Claude `session_id`, the transcript path, the label, and per-turn metadata such as token usage and cost
- it is also how the wrapper resumes the same Claude conversation on the next turn

Recommended usage:

```powershell
python C:\Users\Matthew\.codex\skills\claude-cli\scripts\run_claude.py `
  --conversation working-tree-review `
  --prompt "Review the current local changes. Use git diff to inspect them."
```

That creates:
- a readable transcript file such as `claude-conversations/2026-03-30-21-45-working-tree-review.md`
- a hidden sidecar metadata file such as `claude-conversations/.working-tree-review.meta.json`

Follow-up turns should reuse the same conversation label:

```powershell
python C:\Users\Matthew\.codex\skills\claude-cli\scripts\run_claude.py `
  --conversation working-tree-review `
  --prompt "Re-check the fixes and look for regressions."
```

About `--name`:
- you usually do not need it
- `--name` is only Claude's display label for the session
- when you use `--conversation`, the wrapper already has a stable label and uses it as the Claude session name by default
