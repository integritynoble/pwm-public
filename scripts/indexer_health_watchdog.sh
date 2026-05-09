#!/usr/bin/env bash
# Indexer Health Watchdog — runs every 5 min from cron.
#
# Closes P1 row 2 of PWM_PRELAUNCH_POLISH_PRIORITY_2026-05-08.md.
#
# Polls https://explorer.pwm.platformai.org/api/health. If the
# /api/health response shows status="degraded" for >= 2 consecutive
# checks (i.e. >= 10 min of staleness), restarts the pwm-explorer
# container. Logs everything to /var/log/pwm/indexer_watchdog.log.
#
# Designed to be idempotent and safe to run from anyone's cron — does
# nothing if the explorer is healthy.
#
# Required: docker, curl, jq, python3
# Recommended cron entry on agent-prod (every 5 minutes):
#     */5 * * * * /home/spiritai/pwm/Physics_World_Model/pwm/scripts/indexer_health_watchdog.sh >> /var/log/pwm/indexer_watchdog.log 2>&1
#
# Optional env vars:
#     PWM_HEALTH_URL        — explorer health endpoint (default: prod URL)
#     PWM_CONTAINER_NAME    — docker container name (default: pwm-explorer)
#     PWM_DEGRADED_STATE    — counter file (default: /tmp/pwm_degraded_count)
#     PWM_DEGRADED_THRESHOLD — restart after N consecutive degraded checks (default: 2 → 10 min)
#     PWM_WEBHOOK_URL       — optional Discord/Slack/etc. webhook for alerts

set -uo pipefail

HEALTH_URL="${PWM_HEALTH_URL:-https://explorer.pwm.platformai.org/api/health}"
CONTAINER="${PWM_CONTAINER_NAME:-pwm-explorer}"
STATE_FILE="${PWM_DEGRADED_STATE:-/tmp/pwm_degraded_count}"
THRESHOLD="${PWM_DEGRADED_THRESHOLD:-2}"
WEBHOOK="${PWM_WEBHOOK_URL:-}"
TS="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

log() { printf "[%s] %s\n" "$TS" "$*"; }

notify() {
    local msg="$1"
    log "$msg"
    if [[ -n "$WEBHOOK" ]]; then
        curl -s --max-time 5 -X POST "$WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "$(printf '{"content":"PWM watchdog %s: %s"}' "$TS" "$msg")" \
            >/dev/null || true
    fi
}

# Read /api/health
RESPONSE=$(curl -sf --max-time 8 "$HEALTH_URL" 2>/dev/null || echo "")
if [[ -z "$RESPONSE" ]]; then
    notify "FAIL: /api/health unreachable; container may be down"
    # Try to restart anyway
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
        log "container is up but /api/health unreachable; investigating not restarting"
    else
        notify "container ${CONTAINER} not running; attempting docker start"
        docker start "$CONTAINER" 2>&1 | head -5
    fi
    exit 1
fi

STATUS=$(echo "$RESPONSE" | python3 -c 'import sys, json; print(json.load(sys.stdin).get("status",""))' 2>/dev/null || echo "?")
LAST_BLOCK=$(echo "$RESPONSE" | python3 -c 'import sys, json; print(json.load(sys.stdin).get("last_indexed_block",0))' 2>/dev/null || echo "0")

if [[ "$STATUS" == "healthy" ]] || [[ "$STATUS" == "bootstrapping" ]]; then
    # Reset counter on green
    echo 0 > "$STATE_FILE"
    log "OK: status=$STATUS last_block=$LAST_BLOCK"
    exit 0
fi

# status is "degraded" or unknown
COUNT=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
COUNT=$((COUNT + 1))
echo "$COUNT" > "$STATE_FILE"

if [[ "$COUNT" -lt "$THRESHOLD" ]]; then
    log "WARN: status=$STATUS last_block=$LAST_BLOCK (degraded count=$COUNT, threshold=$THRESHOLD; not yet restarting)"
    exit 0
fi

# Threshold hit — restart
notify "RESTART: status=$STATUS last_block=$LAST_BLOCK (degraded $COUNT consecutive checks ≈ $((COUNT * 5)) min) — restarting container"

if docker restart "$CONTAINER" >/dev/null 2>&1; then
    sleep 8
    NEW_RESPONSE=$(curl -sf --max-time 8 "$HEALTH_URL" 2>/dev/null || echo "")
    NEW_STATUS=$(echo "$NEW_RESPONSE" | python3 -c 'import sys, json; print(json.load(sys.stdin).get("status",""))' 2>/dev/null || echo "?")
    if [[ "$NEW_STATUS" == "healthy" ]] || [[ "$NEW_STATUS" == "bootstrapping" ]]; then
        notify "RECOVERED: status=$NEW_STATUS after restart"
        echo 0 > "$STATE_FILE"
        exit 0
    else
        notify "RESTART INEFFECTIVE: status=$NEW_STATUS — manual investigation required"
        exit 2
    fi
else
    notify "RESTART FAILED: docker restart $CONTAINER returned non-zero"
    exit 3
fi
