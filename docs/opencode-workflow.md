# Shared OpenCode terminal workflow

The user supervises implementation in an interactive OpenCode session. Codex prepares bounded task instructions; the user-selected OpenCode model implements them; Luna prepares focused review and user-run helpers. The user launches and monitors larger collections, timing runs and training. Keep task-specific prompts and implementation handoffs disposable; retain architecture, decisions, actual results and failure history in canonical docs and project records.

## Identify and address the visible session

From the project root, use `opencode session list` and match the title with the conversation the user has open. Do not infer the visible session from recency or model name. If ambiguous, confirm before sending. For initial verification, send a short read-only task with a distinctive marker and have the user confirm it appears. CLI output alone is not evidence of visible delivery.

The session verified for this project was `ses_f0cb2b2e1ffe7wbI0MsfT217MO` (title at verification: `Python project overview and current status in 10 lines`). Session titles can change; confirm the ID again if the visible conversation changes.

## Send one bounded implementation task

From the project directory, continue the confirmed session, explicitly select Build mode, and attach the task file:

```sh
opencode run \
  --session CONFIRMED_SESSION_ID \
  --agent build \
  --file PATH_TO_TASK.md \
  'Reread AGENTS.md, status.md and TODO.md. Implement only the attached scope and stop after its handoff.' \
  > work/opencode-task.log 2>&1
```

Use one task at a time. Specify allowed files, interfaces, exclusions, and the completion criterion. Request a concise on-disk handoff. Read updated project records because the agent may not have incorporated later filesystem changes. Keep transient logs in `work/`; do not copy raw code or large logs into the design chat.

The `--agent build` flag matters: one earlier task inherited Plan mode and returned a plan without editing files. The user's visible-session experiment verified prompt delivery after confirming the right session. It did not measure whether persistent context improves task speed.

For automated completion notices, use [notification-workflow.md](notification-workflow.md). Direct queue acceptance alone is not proof that a message appeared in the intended chat.

## Current session update — 2026-10-01

User identified `Overview of Python files, rig, NN bot, and training rig` as the visible conversation: `ses_f09b671eaffeJHQOKjugvgpYJR`. Notifications were registered to this chat and session, and read-only marker BUNNY-LIVE-HELLO-02 dispatched. User confirmation of visible marker is pending. The previous session responded to BUNNY-HELLO-01 but was the wrong visible conversation.

## User-selected model and reasoning — 2026-10-02

Continue verified session ses_f09b671eaffeJHQOKjugvgpYJR. Omit model/reasoning flags; the user controls those in OpenCode. Keep implementation --agent build, one bounded task at a time, allowed files/interfaces/exclusions/completion criterion. Avoid repeated broad repository onboarding for short edits; provide relevant current facts and focused reads. Observe elapsed time and correction/scope drift evidence before claiming degradation or speed improvements.

## Visible-session routing correction — 2026-10-02

User reports hello was routed to the wrong visible terminal session. Earlier return-trip verification proves notification delivery from the addressed session only, not that the terminal displayed it. Do not treat that as visible-session verification.

Read-only investigation: interactive opencode process on pts/1 has cwd /home/paul/dev/othello but no --session argument. Installed2.0.22 session list describes saved top-level sessions; session.active API describes foreground execution drains, not displayed clients, and returned empty while idle. session.view marks idle notification viewed; it is not a current-session query. Terminal state /home/paul/.local/state/opencode/latest/tui/tabs.json contained no Othello tabs. App terminal reader found no attached terminal. These checks do not identify a displayed conversation.

Before dispatch, obtain the conversation title/sessionID actually displayed by the user, map exact title through session list, and resolve ambiguity rather than using recency or yesterday's registration. Confirm marker appears in that terminal; notification return alone is insufficient. No new message sent during this investigation. Current session identity pending user response.

- User identified displayed title Date reference: 2 Oct 2026. Server-wide opencode api session.list resolved exact title to ses_f033c2b2bffebSUyg2NWGzTWRA, location /home/paul/dev/othello, agentbuild. Project-filtered opencode session list omitted this session. Use server-wide API list matched to user-visible title/ID, not CLI list alone. Notification registration refreshed; corrected hello marker OPENCODE-HELLO-20261002-02 to be dispatched without model/reasoning overrides. Visible terminal receipt pending.

- 2026-10-02: User explicitly confirms OPENCODE-HELLO-20261002-02 appeared in the open terminal. Current visible session verified: Date reference: 2 Oct 2026, ses_f033c2b2bffebSUyg2NWGzTWRA. User-selected model today: DeepSeek Flash4.1. Continue without model/reasoning overrides; tightly bounded tasks, performance judged from observed timings/corrections.
