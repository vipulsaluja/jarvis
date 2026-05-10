---
name: next
description: >
  Jarvis project work resumption skill. Use this skill whenever the user types /next,
  "what's next", "next task", "resume", or "continue working" in the Jarvis project.
  It identifies the current milestone from docs/milestones/current, creates a task breakdown if one
  doesn't exist yet, and picks up the next pending or in-progress task — so the user
  can /clear and come back without losing their place. Always invoke this skill at the
  start of a Jarvis work session.
---

# /next — Resume Jarvis Work

You are picking up work on the Jarvis project. The goal is to always land on the right
next action with zero manual coordination from the user.

## Step 1 — Find the current milestone

Read `docs/milestones/current`. It contains a single milestone ID (e.g. `M0`).

If the file doesn't exist, tell the user and stop — this skill only works inside the
Jarvis project directory.

The milestone name and description are in `docs/roadmap.md` if needed.

## Step 2 — Check for a task breakdown

Look for `docs/milestones/{milestone-id}-tasks.md` (e.g. `docs/milestones/M0-tasks.md`).

---

### If the breakdown file does NOT exist → create it

Read the milestone's full description from `docs/roadmap.md`. Use it to produce a
detailed, actionable task breakdown — not a restatement of the milestone description,
but concrete steps a developer would actually execute one at a time.

Good tasks are:
- Specific enough that "done" is unambiguous (a file exists, a function works, a
  decision is written down)
- Small enough to complete in one focused session
- Ordered so each one builds on the previous

Save the breakdown to `docs/milestones/{milestone-id}-tasks.md` using this format:

```markdown
# {Milestone ID} — {Milestone Name}: Task Breakdown

## Progress
- [ ] = pending  [~] = in progress  [x] = done

## Tasks
- [ ] T1: {task title}
  {1-2 sentence description of what "done" looks like}

- [ ] T2: {task title}
  {1-2 sentence description of what "done" looks like}
```

After saving, tell the user: "I've created the task breakdown for {milestone}. Here's
what we'll work through:" and show the task list. Then ask: "Shall I start on T1 now,
or do you want to adjust the breakdown first?"

Wait for the user's response before proceeding.

---

### If the breakdown file DOES exist → resume work

Read the file. Scan for tasks in this priority order:
1. First task marked `[~]` (in progress — a previous session started this)
2. First task marked `[ ]` (pending — next one to start)

If you find a `[~]` task, tell the user: "Picking up where we left off: **{task}**"
and continue working on it.

If you find a `[ ]` task, update its status to `[~]` in the file, then tell the user:
"Starting next task: **{task}**" and begin working on it.

If all tasks are `[x]`, the milestone is complete — go to Step 3.

## Step 3 — Handle milestone completion

If all tasks in the breakdown are `[x]`:

1. Tell the user: "**{Milestone ID} is complete.** All tasks are done."
2. Show a one-line summary of what was accomplished.
3. Ask: "Ready to move to the next milestone?"
4. If yes, write the next milestone ID (e.g. `M1`) to `docs/milestones/current`,
   replacing the current value. Then run Step 1 again for the new milestone.

## Marking tasks complete

As you work, update task statuses in the breakdown file in real time:
- When you start a task: `[ ]` → `[~]`
- When you finish a task: `[~]` → `[x]`

Don't batch these updates — update immediately when the state changes. This is what
makes `/clear` + `/next` work correctly: the file is the source of truth.

## Tone

Be direct. The user knows the project. Skip preamble — name the task, do the work.
One sentence of context is enough before diving in.
