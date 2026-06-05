#!/bin/zsh
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export CODEX_HOME="${CODEX_HOME:-/Users/han/.codex}"

REPO="/Users/han/Code/morning-news"
PROMPT_FILE="$REPO/tools/draft_prompt.md"
PERSONAL_AUTOMATION="/Users/han/Code/codex-personal-automation"
CICC_ROOT="/Users/han/Desktop/University/Intern/2025 intern application/CICC"
LOG_DIR="$CODEX_HOME/automations/morning-news/logs"
LOCK_DIR="$CODEX_HOME/automations/morning-news/run.lock"

mkdir -p "$LOG_DIR"

STAMP="$(date '+%Y%m%d-%H%M%S')"
LOG_FILE="$LOG_DIR/$STAMP-codex-exec.log"
LAST_MESSAGE_FILE="$LOG_DIR/$STAMP-last-message.md"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "$(date '+%Y-%m-%d %H:%M:%S %Z') another Morning News run is active: $LOCK_DIR" | tee -a "$LOG_FILE"
  exit 75
fi

cleanup() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

{
  echo "Morning News automation run"
  echo "Started: $(date '+%Y-%m-%d %H:%M:%S %Z %z')"
  echo "Repo: $REPO"
  echo "Prompt: $PROMPT_FILE"
  echo "Codex: $(command -v codex)"
  echo
} >> "$LOG_FILE"

if [[ "${MORNING_NEWS_DRY_RUN:-0}" == "1" ]]; then
  {
    echo "Dry run only. Command would be:"
    echo "codex exec --search --dangerously-bypass-approvals-and-sandbox -C \"$REPO\" --add-dir \"$PERSONAL_AUTOMATION\" --add-dir \"$CICC_ROOT\" -m gpt-5.5 -c model_reasoning_effort=\\\"high\\\" -o \"$LAST_MESSAGE_FILE\" - < \"$PROMPT_FILE\""
  } >> "$LOG_FILE"
  echo "$LOG_FILE"
  exit 0
fi

cd "$REPO"

codex exec \
  --search \
  --dangerously-bypass-approvals-and-sandbox \
  -C "$REPO" \
  --add-dir "$PERSONAL_AUTOMATION" \
  --add-dir "$CICC_ROOT" \
  -m gpt-5.5 \
  -c 'model_reasoning_effort="high"' \
  -o "$LAST_MESSAGE_FILE" \
  - < "$PROMPT_FILE" >> "$LOG_FILE" 2>&1

STATUS=$?

{
  echo
  echo "Finished: $(date '+%Y-%m-%d %H:%M:%S %Z %z')"
  echo "Exit status: $STATUS"
  echo "Last message: $LAST_MESSAGE_FILE"
} >> "$LOG_FILE"

exit "$STATUS"
