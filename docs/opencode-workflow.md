# Shared OpenCode terminal workflow

The user supervises implementation in an interactive OpenCode session. Codex prepares bounded task instructions; Space Bunny Free implements them; Luna prepares focused review and user-run helpers. The user launches and monitors larger collections, timing runs and training. Keep task-specific prompts and implementation handoffs disposable; retain architecture, decisions, actual results and failure history in canonical docs and project records.

## Identify and address the visible session

From the project root, use `opencode session list` and match the title with the conversation the user has open. Do not infer the visible session from recency or model name. If ambiguous, confirm before sending. For initial verification, send a short read-only task with a distinctive marker and have the user confirm it appears. CLI output alone is not evidence of visible delivery.

The session verified for this project was `ses_f0cb2b2e1ffe7wbI0MsfT217MO` (title at verification: `Python project overview and current status in 10 lines`). Session titles can change; confirm the ID again if the visible conversation changes.

## Send one bounded implementation task

From the project directory, continue the confirmed session, explicitly select Build mode, and attach the task file:

```sh
opencode run \
  --session CONFIRMED_SESSION_ID \
  --model opencode/space-bunny-free \
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
