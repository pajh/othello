# OpenCode completion notifications

The project uses a small Bash control script and a local OpenCode V2 plugin. Notifications are manually enabled/disabled; registration explicitly pairs the target Codex chat with the watched OpenCode session. Do not infer routing from PIDs, process names or most-recent-session order.

## Controls

From the repository root, refresh the target before dispatching work, preserving its current enabled state:

```sh
bash scripts/notify_codex.sh register CODEX_THREAD_UUID OPENCODE_SESSION_ID
bash scripts/notify_codex.sh status
bash scripts/notify_codex.sh on
# later, or whenever notices should stop:
bash scripts/notify_codex.sh off
```

The active Codex thread ID is available as `CODEX_THREAD_ID`; confirm it belongs to the intended design chat. The current watched OpenCode session previously verified for this project is `ses_f0cb2b2e1ffe7wbI0MsfT217MO`; confirm it is still the user's visible session before registering. The controls and state paths are implemented in `scripts/notify_codex.sh` and `work/codex-notify/`.

The script makes one bounded `codex queue --thread THREAD --message TEXT` attempt with safely separated arguments. It does not start or restart a daemon. A successful queue command is not by itself proof of visible receipt; verify the message in the intended chat before claiming delivery.

## Local hook and delivery evidence

Project root `opencode.json` loads `./plugins/codex-notify` as a directory. This installed build emits `session.execution.succeeded` with `data.sessionID`; the plugin reads the watched session's latest completed final assistant text and invokes the script. The API research and sources are in [notify-hook-api.md](notify-hook-api.md). Runtime checks established the directory path and event fields.

Automatic notification `OPENCODE-HOOK-IDLE-03` was visibly received and acknowledged after the design chat became idle. An earlier queue-accepted notice during an active turn was not visibly received. Thus idle delivery has been verified; delivery during active turns remains uncertain. Notifications were last recorded as enabled. Check `bash scripts/notify_codex.sh status` and the local hook/notification logs rather than assuming current state.

The plugin is project-local; no global package was installed. If it is not loaded, verify `opencode.json`, then use the installed version's documented reload flow without interrupting active work. Avoid polling: dispatch one task, end the design turn, and review its saved handoff when the notification arrives.

## Return-trip verification — 2026-10-02

OPENCODE-HELLO-20261002-01 returned visibly to design chat01a0fc6d-1e07-70f3-874f-1fa07d1efb6c from session ses_f09b671eaffeJHQOKjugvgpYJR. Dispatched with --agent build and without model/reasoning overrides. This verifies this hello round trip; no broader active-turn reliability claim.

## Visible-session routing correction — 2026-10-02

User reports hello was routed to the wrong visible terminal session. Earlier return-trip verification proves notification delivery from the addressed session only, not that the terminal displayed it. Do not treat that as visible-session verification.

Read-only investigation: interactive opencode process on pts/1 has cwd /home/paul/dev/othello but no --session argument. Installed2.0.22 session list describes saved top-level sessions; session.active API describes foreground execution drains, not displayed clients, and returned empty while idle. session.view marks idle notification viewed; it is not a current-session query. Terminal state /home/paul/.local/state/opencode/latest/tui/tabs.json contained no Othello tabs. App terminal reader found no attached terminal. These checks do not identify a displayed conversation.

Before dispatch, obtain the conversation title/sessionID actually displayed by the user, map exact title through session list, and resolve ambiguity rather than using recency or yesterday's registration. Confirm marker appears in that terminal; notification return alone is insufficient. No new message sent during this investigation. Current session identity pending user response.

- User identified displayed title Date reference: 2 Oct 2026. Server-wide opencode api session.list resolved exact title to ses_f033c2b2bffebSUyg2NWGzTWRA, location /home/paul/dev/othello, agentbuild. Project-filtered opencode session list omitted this session. Use server-wide API list matched to user-visible title/ID, not CLI list alone. Notification registration refreshed; corrected hello marker OPENCODE-HELLO-20261002-02 to be dispatched without model/reasoning overrides. Visible terminal receipt pending.

- 2026-10-02: User explicitly confirms OPENCODE-HELLO-20261002-02 appeared in the open terminal. Current visible session verified: Date reference: 2 Oct 2026, ses_f033c2b2bffebSUyg2NWGzTWRA. User-selected model today: DeepSeek Flash4.1. Continue without model/reasoning overrides; tightly bounded tasks, performance judged from observed timings/corrections.
