// Minimal OpenCode V2 completion hook.
//
// Forwards the full final assistant summary of the watched session into the
// registered Codex thread by calling scripts/notify_codex.sh. Node built-ins
// only: no SDK import, no model call, no shell interpolation. The script
// owns routing, the on/off setting, the codex executable and the timeout.
import { spawn } from "node:child_process"
import { appendFileSync, mkdirSync, readFileSync } from "node:fs"
import { dirname, join, resolve } from "node:path"
import { fileURLToPath } from "node:url"

const PLUGIN_DIR = dirname(fileURLToPath(import.meta.url))
const ROOT = resolve(PLUGIN_DIR, "..", "..")
const STATE_DIR = join(ROOT, "work", "codex-notify")
const SCRIPT = join(ROOT, "scripts", "notify_codex.sh")
const LOG = join(STATE_DIR, "hook.log")

// sessionID -> id of the final assistant message already handled.
const handled = new Map()
let controller

// Diagnostics only: short lines, no message text, no tool or reasoning dumps.
function log(event, detail = "") {
  try {
    mkdirSync(STATE_DIR, { recursive: true })
    appendFileSync(LOG, `${new Date().toISOString()} ${event} ${detail}\n`)
  } catch {}
}

function readState(name) {
  try {
    return readFileSync(join(STATE_DIR, name), "utf8").trim()
  } catch {
    return ""
  }
}

function short(value) {
  return String(value ?? "").replaceAll("\n", " ").slice(0, 200)
}

// Latest completed assistant response: full text parts only, in order.
function finalSummary(context) {
  const messages = Array.isArray(context)
    ? context
    : Array.isArray(context?.messages)
      ? context.messages
      : Array.isArray(context?.data)
        ? context.data
        : null
  if (!messages) {
    log("unexpected_context", `keys=${Object.keys(context ?? {}).join(",") || typeof context}`)
    return null
  }
  for (let index = messages.length - 1; index >= 0; index--) {
    const message = messages[index]
    if (message?.type !== "assistant" || message?.finish !== "stop") continue
    const text = (message.content ?? [])
      .filter((entry) => entry?.type === "text")
      .map((entry) => entry.text ?? "")
      .join("\n")
    return {
      id: message.id ?? "",
      text,
      type: message.type,
      finish: message.finish,
      partTypes: (message.content ?? []).map((entry) => entry?.type ?? "?").join(","),
    }
  }
  return null
}

function send(sessionID, thread, text) {
  const child = spawn("bash", [SCRIPT, "send", sessionID, text], {
    stdio: ["ignore", "ignore", "pipe"],
  })
  child.on("error", (err) => log("spawn_error", `session=${sessionID} error=${short(err.message)}`))
  child.stderr?.on("data", (chunk) => log("script_stderr", `session=${sessionID} ${short(chunk)}`))
  child.on("close", (code) =>
    log("dispatched", `session=${sessionID} thread=${thread || "unset"} exit=${code}`),
  )
}

async function handle(ctx, event) {
  try {
    // Observed on opencode v2.0.20: a finished response arrives as
    // session.execution.succeeded with the session id at data.sessionID.
    // No session.idle event was seen for this session.
    if (event?.type !== "session.execution.succeeded") return
    const sessionID = event?.data?.sessionID
    if (!sessionID) {
      log("unexpected_event", `type=${event?.type} keys=${Object.keys(event ?? {}).join(",")}`)
      return
    }
    const state = {
      enabled: readState("enabled"),
      session: readState("session.id"),
      thread: readState("thread.id"),
    }
    if (state.enabled !== "on" || !state.session || state.session !== sessionID) return
    const latest = finalSummary(await ctx.session.context({ sessionID }))
    if (!latest?.text) return
    log("extract_ok",
      `session=${sessionID} message=${latest.id || "none"}`
      + ` type=${latest.type} finish=${latest.finish} part_types=${latest.partTypes || "none"}`)
    if (latest.id && handled.get(sessionID) === latest.id) return
    if (latest.id) handled.set(sessionID, latest.id)
    send(sessionID, state.thread, latest.text)
  } catch (err) {
    log("handler_error", `error=${short(err?.message ?? err)}`)
  }
}

export default {
  id: "local.codex-notify",
  async setup(ctx) {
    if (typeof ctx?.event?.subscribe !== "function" || typeof ctx?.session?.context !== "function") {
      log("blocker=missing_api",
        `event.subscribe=${typeof ctx?.event?.subscribe} session.context=${typeof ctx?.session?.context}`)
      return
    }
    try {
      // Baseline the watched session so an already-finished summary is not
      // forwarded later; only summaries completed after this setup count.
      const sessionID = readState("session.id")
      if (!sessionID) {
        log("baseline", "reason=no_registered_session")
      } else {
        const latest = finalSummary(await ctx.session.context({ sessionID }))
        if (latest?.id) {
          handled.set(sessionID, latest.id)
          log("baseline", `session=${sessionID} message=${latest.id}`)
        } else {
          log("baseline", `session=${sessionID} message=none`)
        }
      }
    } catch (err) {
      log("baseline_error", `error=${short(err?.message ?? err)}`)
    }

    controller = new AbortController()
    void (async () => {
      try {
        for await (const event of await ctx.event.subscribe({ signal: controller.signal })) {
          await handle(ctx, event)
        }
      } catch (err) {
        log("subscribe_error", `error=${short(err?.message ?? err)}`)
      } finally {
        controller.abort()
      }
    })()
  },
}
