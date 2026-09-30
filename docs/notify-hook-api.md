# OpenCode V2 completion-hook API notes

Read-only API research on 2026-09-30 for the installed OpenCode v2.0.20
integration. No plugin was loaded and no OpenCode task was run.

## Verified access path

- The official V2 plugin docs expose `ctx.event.subscribe({ signal })` as
  an async event stream and show `ctx.session.context({ sessionID })` for
  reading session messages.
- The official V2 event schema/types define `session.idle` with
  `event.properties.sessionID: string`; there is no message ID or final
  text in that event. The matching session context must be read after the
  event.
- The current official session-message schema uses a tagged union. An
  assistant entry has `type: "assistant"`, `content: AssistantContent[]`,
  optional `finish`, and optional completion time. Content variants are
  `text`, `reasoning`, and `tool`. A final-output extractor should select
  the latest completed assistant message and join only its `content`
  entries whose `type === "text"`; this excludes reasoning and tool
  payloads.

The provided `work/bunny-overview-session.json` corroborates a current
export shape of top-level `messages` entries tagged with `type`, not the
older `{info, parts}` representation. Assistant text is in `content`;
tool calls and reasoning are separately tagged. In this sample the
assistant messages ending the work have `finish: "stop"` and include text
content. This is observed export data, not a runtime call to the V2
plugin API. A conservative implementation can require `finish ===
"stop"` when selecting the latest assistant message; if the installed
v2.0.20 returns another finish value, skip rather than forwarding an
intermediate/tool-call message.

## Sources and limits

- [OpenCode V2 plugin docs](https://opencode.ai/v2/docs/build/plugins/):
  event subscription and `ctx.session.context` examples/types.
- [OpenCode V2 session-message schema](https://github.com/anomalyco/opencode/blob/dev/packages/schema/src/session-message.ts):
  assistant metadata and tagged content union.
- [OpenCode V2 session status event schema](https://github.com/anomalyco/opencode/blob/dev/packages/schema/src/session-status-event.ts)
  and [generated event types](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts):
  `session.idle` properties.

The official V2 docs establish the accessor and event stream, and the
official source establishes the current schema. The installed v2.0.20
runtime was not queried because invoking the binary currently fails on a
read-only log path. Confirm event delivery, returned context shape, and
`finish` semantics with a small local plugin smoke before treating them
as validated for that exact installed build.
