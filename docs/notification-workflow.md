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
