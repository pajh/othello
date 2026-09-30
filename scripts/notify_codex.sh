#!/usr/bin/env bash
# Queue a short notice into a Codex design thread on behalf of OpenCode.
#
# General-purpose Bash, independent of the Othello project. Routing state
# and the log are resolved from this script's own location, so the command
# behaves identically from any working directory.
#
# Usage:
#   notify_codex.sh register THREAD_UUID OPENCODE_SESSION_ID
#   notify_codex.sh on | off | status
#   notify_codex.sh send OPENCODE_SESSION_ID MESSAGE
#
# Exit status:
#   0  success, or a deliberate skip (unregistered, disabled, other
#      session, no codex executable) that must not fail the caller
#   1  state problem, such as enabling without a registration
#   2  usage or validation error
#
# The message is always passed as one quoted argument, newlines and all,
# and is never evaluated as shell code. State files are read as data and
# never sourced. The Codex thread is always the explicitly registered
# value; no PID or process is ever inspected to guess a conversation.

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
STATE_DIR="$SCRIPT_DIR/../work/codex-notify"
THREAD_FILE="$STATE_DIR/thread.id"
SESSION_FILE="$STATE_DIR/session.id"
ENABLED_FILE="$STATE_DIR/enabled"
LOG_FILE="$STATE_DIR/notify.log"

# Used when "codex" is not on PATH; this is the executable the user
# verified by hand for direct queue delivery.
CODEX_FALLBACK=/usr/lib/chatgpt/resources/codex

# Bounded call, no retries, no daemon start or restart.
QUEUE_TIMEOUT_SECONDS=${QUEUE_TIMEOUT_SECONDS:-10}

usage() {
    cat >&2 <<'USAGE'
usage: notify_codex.sh <command> [arguments]

  register THREAD_UUID OPENCODE_SESSION_ID
        save the Codex thread and the watched OpenCode session; the
        current on/off setting is kept, and is off only when unset
  on      enable notifications for the registered session
  off     disable notifications
  status  show the current registration and enablement
  send OPENCODE_SESSION_ID MESSAGE
        queue one message, if notifications are on and the session matches

State and log: work/codex-notify/ (thread.id, session.id, enabled,
notify.log), beside the repository root.
USAGE
}

usage_error() {
    printf 'error: %s\n' "$1" >&2
    usage
    exit 2
}

timestamp() {
    date -u +%Y-%m-%dT%H:%M:%SZ
}

# Collapse newlines so a multi-line message stays on one log line.
one_line() {
    local text=${1-}
    text=${text//$'\n'/\\n}
    text=${text//$'\r'/}
    printf '%s' "$text"
}

log_line() {
    local level=$1
    shift
    mkdir -p "$STATE_DIR"
    printf '%s level=%s %s\n' "$(timestamp)" "$level" "$*" >> "$LOG_FILE"
}

# Read a state file as data. Prints nothing when the file is absent.
read_value() {
    local path=$1 value
    [ -f "$path" ] || return 0
    IFS= read -r value < "$path" || true
    printf '%s' "$value"
}

# Replace a state file atomically: write a sibling temporary, then rename.
write_value() {
    local path=$1 value=$2 temporary
    temporary="$path.tmp.$$"
    printf '%s\n' "$value" >"$temporary"
    mv -f "$temporary" "$path"
}

is_uuid() {
    [[ $1 =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]
}

is_session() {
    [[ $1 =~ ^ses_[A-Za-z0-9]+$ ]]
}

# Resolve the codex executable: PATH first, then the verified install
# location. Prints the path. Fails when neither exists, in which case the
# caller skips delivery and logs the message as unsent. Nothing here
# starts, restarts or queries a daemon.
resolve_codex_executable() {
    local path
    if path=$(command -v codex 2>/dev/null) && [ -n "$path" ]; then
        printf '%s' "$path"
        return 0
    fi
    if [ -x "$CODEX_FALLBACK" ]; then
        printf '%s' "$CODEX_FALLBACK"
        return 0
    fi
    return 1
}

cmd_register() {
    [ "$#" -eq 2 ] || usage_error "register needs THREAD_UUID OPENCODE_SESSION_ID"
    local thread=$1 session=$2
    is_uuid "$thread" ||
        usage_error "thread must be a UUID such as 01a0f2cb-7f39-7c70-a8e4-3e8a796d3d71"
    is_session "$session" ||
        usage_error "session must look like ses_<alphanumerics>"
    local enabled
    enabled=$(read_value "$ENABLED_FILE")
    [ -n "$enabled" ] || enabled="off"
    mkdir -p "$STATE_DIR"
    write_value "$THREAD_FILE" "$thread"
    write_value "$SESSION_FILE" "$session"
    write_value "$ENABLED_FILE" "$enabled"
    log_line state "event=register thread=$thread session=$session enabled=$enabled"
    printf 'registered thread %s for session %s; notifications %s\n' \
        "$thread" "$session" "$enabled"
    [ "$enabled" = "on" ] || printf 'enable with: %s on\n' "$0"
}

cmd_on() {
    [ "$#" -eq 0 ] || usage_error "on takes no arguments"
    local thread session
    thread=$(read_value "$THREAD_FILE")
    session=$(read_value "$SESSION_FILE")
    if [ -z "$thread" ] || [ -z "$session" ]; then
        log_line error "event=on reason=not_registered"
        printf 'error: no registration; run: %s register THREAD_UUID OPENCODE_SESSION_ID\n' \
            "$0" >&2
        return 1
    fi
    write_value "$ENABLED_FILE" "on"
    log_line state "event=on thread=$thread session=$session"
    printf 'notifications on: session %s -> thread %s\n' "$session" "$thread"
}

cmd_off() {
    [ "$#" -eq 0 ] || usage_error "off takes no arguments"
    mkdir -p "$STATE_DIR"
    write_value "$ENABLED_FILE" "off"
    log_line state "event=off"
    printf 'notifications off\n'
}

cmd_status() {
    [ "$#" -eq 0 ] || usage_error "status takes no arguments"
    local thread session enabled
    thread=$(read_value "$THREAD_FILE")
    session=$(read_value "$SESSION_FILE")
    enabled=$(read_value "$ENABLED_FILE")
    [ -n "$enabled" ] || enabled="off"
    if [ -n "$thread" ] && [ -n "$session" ]; then
        printf 'registered: yes\n'
        printf '  codex thread:   %s\n' "$thread"
        printf '  opencode session: %s\n' "$session"
    else
        printf 'registered: no\n'
    fi
    printf '  notifications: %s\n' "$enabled"
    printf 'state directory: %s\n' "$STATE_DIR"
    printf 'log file: %s\n' "$LOG_FILE"
    printf 'the codex executable is resolved at send time, not here\n'
}

cmd_send() {
    [ "$#" -ge 2 ] || usage_error "send needs OPENCODE_SESSION_ID MESSAGE"
    local session=$1 message=$2
    [ -n "$message" ] || usage_error "message must not be empty"

    local thread registered enabled
    thread=$(read_value "$THREAD_FILE")
    registered=$(read_value "$SESSION_FILE")
    enabled=$(read_value "$ENABLED_FILE")

    if [ -z "$thread" ] || [ -z "$registered" ]; then
        log_line skip "event=send session=$session reason=not_registered"
        printf 'notify_codex: skipped, no registration\n'
        return 0
    fi
    if [ "$enabled" != "on" ]; then
        log_line skip "event=send session=$session thread=$thread reason=disabled"
        printf 'notify_codex: skipped, notifications are off\n'
        return 0
    fi
    if [ "$session" != "$registered" ]; then
        log_line skip "event=send session=$session registered_session=$registered reason=session_mismatch"
        printf 'notify_codex: skipped, %s is not the registered session %s\n' \
            "$session" "$registered"
        return 0
    fi

    local codex_executable
    if ! codex_executable=$(resolve_codex_executable); then
        log_line skip "event=send session=$session thread=$thread reason=codex_executable_missing fallback=$CODEX_FALLBACK message=$(one_line "$message")"
        printf 'notify_codex: skipped, no codex executable (PATH or %s)\n' \
            "$CODEX_FALLBACK" >&2
        printf 'notify_codex: unsent message recorded in %s\n' "$LOG_FILE" >&2
        return 0
    fi
    if ! command -v timeout >/dev/null 2>&1; then
        log_line skip "event=send session=$session thread=$thread reason=timeout_missing message=$(one_line "$message")"
        printf 'notify_codex: skipped, timeout command not found in PATH\n' >&2
        printf 'notify_codex: unsent message recorded in %s\n' "$LOG_FILE" >&2
        return 0
    fi

    local output status
    set +e
    output=$(timeout "$QUEUE_TIMEOUT_SECONDS" "$codex_executable" queue \
        --thread "$thread" --message "$message" 2>&1)
    status=$?
    set -e
    if [ "$status" -eq 0 ]; then
        log_line sent "event=send session=$session thread=$thread executable=$codex_executable output=$(one_line "$output")"
        printf 'notify_codex: queued to thread %s\n' "$thread"
        return 0
    fi
    log_line unsent "event=send session=$session thread=$thread executable=$codex_executable exit=$status output=$(one_line "$output") message=$(one_line "$message")"
    printf 'notify_codex: queue failed with exit %s; unsent message recorded in %s\n' \
        "$status" "$LOG_FILE" >&2
    return 0
}

command=${1:-}
if [ "$#" -gt 0 ]; then
    shift
fi

case "$command" in
    register) cmd_register "$@" ;;
    on) cmd_on "$@" ;;
    off) cmd_off "$@" ;;
    status) cmd_status "$@" ;;
    send) cmd_send "$@" ;;
    help | -h | --help)
        usage
        exit 0
        ;;
    '')
        usage
        exit 2
        ;;
    *)
        usage_error "unknown command: $command"
        ;;
esac
