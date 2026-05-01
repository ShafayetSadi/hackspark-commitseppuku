#!/bin/sh
set -eu

COMPOSE_CMD=${COMPOSE_CMD:-"docker compose -f docker-compose.yml"}
BASE_URL=${BASE_URL:-"http://localhost:8000"}
UV_CACHE_DIR=${UV_CACHE_DIR:-"/tmp/uv-cache"}
REQUEST_DELAY_SECONDS=${REQUEST_DELAY_SECONDS:-5}
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT HUP INT TERM

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0
RUN_ID=$(date +%s)

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS %s\n' "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf 'FAIL %s\n' "$1"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  printf 'WARN %s\n' "$1"
}

section() {
  printf '\n== %s ==\n' "$1"
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "$1" >&2
    exit 1
  fi
}

http_request() {
  method=$1
  url=$2
  body=${3-}
  headers_file=$4
  body_file=$5
  auth_header=${6-}

  if [ -n "$body" ]; then
    if [ -n "$auth_header" ]; then
      curl -sS -X "$method" "$url" \
        -H "Content-Type: application/json" \
        -H "$auth_header" \
        -D "$headers_file" \
        -o "$body_file" \
        --data "$body"
    else
      curl -sS -X "$method" "$url" \
        -H "Content-Type: application/json" \
        -D "$headers_file" \
        -o "$body_file" \
        --data "$body"
    fi
  else
    if [ -n "$auth_header" ]; then
      curl -sS -X "$method" "$url" \
        -H "$auth_header" \
        -D "$headers_file" \
        -o "$body_file"
    else
      curl -sS -X "$method" "$url" \
        -D "$headers_file" \
        -o "$body_file"
    fi
  fi

  request_status=$?
  sleep "$REQUEST_DELAY_SECONDS"
  return "$request_status"
}

http_status() {
  awk 'toupper($1) ~ /^HTTP/ {code=$2} END {print code}' "$1"
}

json_has_key() {
  python3 - "$1" "$2" <<'PY'
import json
import sys

path = sys.argv[2].split(".")
with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)
node = data
for part in path:
    if not isinstance(node, dict) or part not in node:
        raise SystemExit(1)
    node = node[part]
raise SystemExit(0)
PY
}

json_array_nonempty() {
  python3 - "$1" "$2" <<'PY'
import json
import sys

path = sys.argv[2].split(".")
with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)
node = data
for part in path:
    if not isinstance(node, dict) or part not in node:
        raise SystemExit(1)
    node = node[part]
if not isinstance(node, list) or not node:
    raise SystemExit(1)
PY
}

json_array_length_equals() {
  python3 - "$1" "$2" "$3" <<'PY'
import json
import sys

path = sys.argv[2].split(".")
expected = int(sys.argv[3])
with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)
node = data
for part in path:
    if not isinstance(node, dict) or part not in node:
        raise SystemExit(1)
    node = node[part]
if not isinstance(node, list) or len(node) != expected:
    raise SystemExit(1)
PY
}

json_array_length_at_most() {
  python3 - "$1" "$2" "$3" <<'PY'
import json
import sys

path = sys.argv[2].split(".")
expected = int(sys.argv[3])
with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)
node = data
for part in path:
    if not isinstance(node, dict) or part not in node:
        raise SystemExit(1)
    node = node[part]
if not isinstance(node, list) or len(node) > expected:
    raise SystemExit(1)
PY
}

json_feed_items_valid() {
  python3 - "$1" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)
feed = data.get("feed")
if not isinstance(feed, list):
    raise SystemExit(1)
for item in feed:
    if not isinstance(item, dict):
        raise SystemExit(1)
    for key in ("rentalId", "productId", "rentalStart", "rentalEnd"):
        if key not in item:
            raise SystemExit(1)
PY
}

json_recommendations_valid() {
  python3 - "$1" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)
recommendations = data.get("recommendations")
if not isinstance(recommendations, list):
    raise SystemExit(1)
for item in recommendations:
    if not isinstance(item, dict):
        raise SystemExit(1)
    for key in ("productId", "name", "category", "score"):
        if key not in item:
            raise SystemExit(1)
PY
}

extract_json_value() {
  python3 - "$1" "$2" <<'PY'
import json
import sys

path = sys.argv[2].split(".")
with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)
node = data
for part in path:
    node = node[part]
print(node)
PY
}

register_and_login() {
  register_headers="$TMP_DIR/register.headers"
  register_body="$TMP_DIR/register.json"
  register_email="chapter3-${RUN_ID}@example.com"
  register_payload=$(printf '{"full_name":"Chapter Three User","email":"%s","password":"password123"}' "$register_email")
  TOKEN=""

  if http_request POST "$BASE_URL/users/register" "$register_payload" "$register_headers" "$register_body"; then
    register_status=$(http_status "$register_headers")
    if [ "$register_status" = "201" ] || [ "$register_status" = "200" ]; then
      if json_has_key "$register_body" "access_token"; then
        pass "register returns an access_token for Chapter 3 verification"
        TOKEN=$(extract_json_value "$register_body" "access_token")
      else
        fail "register response missing access_token"
      fi
    else
      fail "register returned HTTP $register_status"
    fi
  else
    fail "register request is unreachable"
  fi

  if [ -z "$TOKEN" ]; then
    login_headers="$TMP_DIR/login.headers"
    login_body="$TMP_DIR/login.json"
    login_payload=$(printf '{"email":"%s","password":"password123"}' "$register_email")
    if http_request POST "$BASE_URL/users/login" "$login_payload" "$login_headers" "$login_body"; then
      login_status=$(http_status "$login_headers")
      if [ "$login_status" = "200" ] && json_has_key "$login_body" "access_token"; then
        pass "login returns an access_token for Chapter 3 verification"
        TOKEN=$(extract_json_value "$login_body" "access_token")
      else
        fail "login did not return the expected token payload"
      fi
    else
      fail "login request is unreachable"
    fi
  fi

  if [ -n "$TOKEN" ]; then
    AUTH_HEADER="Authorization: Bearer $TOKEN"
  else
    AUTH_HEADER=""
  fi
}

need_cmd curl
need_cmd docker
need_cmd python3
need_cmd sh

section "Stack"
if ! $COMPOSE_CMD config >/dev/null; then
  printf 'docker compose config failed\n' >&2
  exit 1
fi
pass "docker compose config renders successfully"

if $COMPOSE_CMD ps >/dev/null 2>&1; then
  pass "docker compose ps is available"
else
  fail "docker compose ps failed"
fi

section "Targeted Tests"
if command -v uv >/dev/null 2>&1; then
  if UV_CACHE_DIR="$UV_CACHE_DIR" uv run python -m pytest \
    tests/unit/test_chapter3_analytics.py \
    tests/unit/test_chapter3_rentals.py \
    tests/unit/test_chapter3_gateway.py >/dev/null; then
    pass "Chapter 3 unit tests pass"
  else
    fail "Chapter 3 unit tests failed"
  fi
else
  warn "uv is not installed; skipping Chapter 3 unit tests"
fi

section "Auth Setup"
register_and_login
if [ -n "${AUTH_HEADER:-}" ]; then
  pass "JWT acquired for protected Chapter 3 endpoints"
else
  fail "could not obtain JWT for protected Chapter 3 endpoints"
fi

section "P11 Peak Window"
p11_headers="$TMP_DIR/p11.headers"
p11_body="$TMP_DIR/p11.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/analytics/peak-window?from=2024-01&to=2024-06" \
  "" "$p11_headers" "$p11_body" "$AUTH_HEADER"; then
  p11_status=$(http_status "$p11_headers")
  if [ "$p11_status" = "200" ]; then
    pass "P11 peak-window route returns HTTP 200"
  else
    fail "P11 peak-window route returned HTTP $p11_status"
  fi

  for key in from to peakWindow peakWindow.from peakWindow.to peakWindow.totalRentals; do
    if json_has_key "$p11_body" "$key"; then
      pass "P11 response includes $key"
    else
      fail "P11 response missing $key"
    fi
  done
else
  fail "P11 peak-window route is unreachable"
fi

p11_invalid_headers="$TMP_DIR/p11-invalid.headers"
p11_invalid_body="$TMP_DIR/p11-invalid.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/analytics/peak-window?from=2024-1&to=2024-06" \
  "" "$p11_invalid_headers" "$p11_invalid_body" "$AUTH_HEADER"; then
  p11_invalid_status=$(http_status "$p11_invalid_headers")
  if [ "$p11_invalid_status" = "400" ]; then
    pass "P11 invalid month format returns 400"
  else
    fail "P11 invalid month format returned HTTP $p11_invalid_status instead of 400"
  fi
else
  fail "P11 invalid-month probe is unreachable"
fi

p11_order_headers="$TMP_DIR/p11-order.headers"
p11_order_body="$TMP_DIR/p11-order.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/analytics/peak-window?from=2024-06&to=2024-01" \
  "" "$p11_order_headers" "$p11_order_body" "$AUTH_HEADER"; then
  p11_order_status=$(http_status "$p11_order_headers")
  if [ "$p11_order_status" = "400" ]; then
    pass "P11 reversed month range returns 400"
  else
    fail "P11 reversed month range returned HTTP $p11_order_status instead of 400"
  fi
else
  fail "P11 reversed-range probe is unreachable"
fi

p11_span_headers="$TMP_DIR/p11-span.headers"
p11_span_body="$TMP_DIR/p11-span.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/analytics/peak-window?from=2024-01&to=2025-01" \
  "" "$p11_span_headers" "$p11_span_body" "$AUTH_HEADER"; then
  p11_span_status=$(http_status "$p11_span_headers")
  if [ "$p11_span_status" = "400" ]; then
    pass "P11 month range longer than 12 months returns 400"
  else
    fail "P11 long month range returned HTTP $p11_span_status instead of 400"
  fi
else
  fail "P11 long-range probe is unreachable"
fi

section "P12 Merged Feed"
p12_headers="$TMP_DIR/p12.headers"
p12_body="$TMP_DIR/p12.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/rentals/merged-feed?productIds=12,47,88,12&limit=10" \
  "" "$p12_headers" "$p12_body" "$AUTH_HEADER"; then
  p12_status=$(http_status "$p12_headers")
  if [ "$p12_status" = "200" ]; then
    pass "P12 merged-feed route returns HTTP 200"
  else
    fail "P12 merged-feed route returned HTTP $p12_status"
  fi

  for key in productIds limit feed; do
    if json_has_key "$p12_body" "$key"; then
      pass "P12 response includes $key"
    else
      fail "P12 response missing $key"
    fi
  done

  if json_array_length_equals "$p12_body" "productIds" "3"; then
    pass "P12 duplicate productIds are deduplicated before returning"
  else
    fail "P12 response did not deduplicate duplicate productIds"
  fi

  if json_feed_items_valid "$p12_body"; then
    pass "P12 feed items keep the expected rental fields"
  else
    fail "P12 feed items are missing expected fields"
  fi
else
  fail "P12 merged-feed route is unreachable"
fi

p12_invalid_ids_headers="$TMP_DIR/p12-invalid-ids.headers"
p12_invalid_ids_body="$TMP_DIR/p12-invalid-ids.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/rentals/merged-feed?productIds=12,,88&limit=10" \
  "" "$p12_invalid_ids_headers" "$p12_invalid_ids_body" "$AUTH_HEADER"; then
  p12_invalid_ids_status=$(http_status "$p12_invalid_ids_headers")
  if [ "$p12_invalid_ids_status" = "400" ]; then
    pass "P12 invalid productIds returns 400"
  else
    fail "P12 invalid productIds returned HTTP $p12_invalid_ids_status instead of 400"
  fi
else
  fail "P12 invalid-productIds probe is unreachable"
fi

p12_invalid_limit_headers="$TMP_DIR/p12-invalid-limit.headers"
p12_invalid_limit_body="$TMP_DIR/p12-invalid-limit.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/rentals/merged-feed?productIds=12,47,88&limit=101" \
  "" "$p12_invalid_limit_headers" "$p12_invalid_limit_body" "$AUTH_HEADER"; then
  p12_invalid_limit_status=$(http_status "$p12_invalid_limit_headers")
  if [ "$p12_invalid_limit_status" = "400" ]; then
    pass "P12 invalid limit returns 400"
  else
    fail "P12 invalid limit returned HTTP $p12_invalid_limit_status instead of 400"
  fi
else
  fail "P12 invalid-limit probe is unreachable"
fi

section "P13 Surge Days"
p13_headers="$TMP_DIR/p13.headers"
p13_body="$TMP_DIR/p13.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/analytics/surge-days?month=2024-03" \
  "" "$p13_headers" "$p13_body" "$AUTH_HEADER"; then
  p13_status=$(http_status "$p13_headers")
  if [ "$p13_status" = "200" ]; then
    pass "P13 surge-days route returns HTTP 200"
  else
    fail "P13 surge-days route returned HTTP $p13_status"
  fi

  for key in month data; do
    if json_has_key "$p13_body" "$key"; then
      pass "P13 response includes $key"
    else
      fail "P13 response missing $key"
    fi
  done

  if json_array_length_equals "$p13_body" "data" "31"; then
    pass "P13 response fills the whole month day-by-day"
  else
    fail "P13 response did not include every day of the month"
  fi
else
  fail "P13 surge-days route is unreachable"
fi

p13_invalid_headers="$TMP_DIR/p13-invalid.headers"
p13_invalid_body="$TMP_DIR/p13-invalid.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/analytics/surge-days?month=2024-3" \
  "" "$p13_invalid_headers" "$p13_invalid_body" "$AUTH_HEADER"; then
  p13_invalid_status=$(http_status "$p13_invalid_headers")
  if [ "$p13_invalid_status" = "400" ]; then
    pass "P13 invalid month format returns 400"
  else
    fail "P13 invalid month format returned HTTP $p13_invalid_status instead of 400"
  fi
else
  fail "P13 invalid-month probe is unreachable"
fi

section "P14 What's In Season"
p14_headers="$TMP_DIR/p14.headers"
p14_body="$TMP_DIR/p14.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/analytics/recommendations?date=2024-06-15&limit=5" \
  "" "$p14_headers" "$p14_body" "$AUTH_HEADER"; then
  p14_status=$(http_status "$p14_headers")
  if [ "$p14_status" = "200" ]; then
    pass "P14 recommendations route returns HTTP 200"
  else
    fail "P14 recommendations route returned HTTP $p14_status"
  fi

  for key in date recommendations; do
    if json_has_key "$p14_body" "$key"; then
      pass "P14 response includes $key"
    else
      fail "P14 response missing $key"
    fi
  done

  if json_recommendations_valid "$p14_body"; then
    pass "P14 recommendations keep the expected enriched product fields"
  else
    fail "P14 recommendations are missing expected fields"
  fi

  if json_array_length_at_most "$p14_body" "recommendations" "5"; then
    pass "P14 respects the requested limit"
  else
    fail "P14 returned more recommendations than requested"
  fi
else
  fail "P14 recommendations route is unreachable"
fi

p14_invalid_date_headers="$TMP_DIR/p14-invalid-date.headers"
p14_invalid_date_body="$TMP_DIR/p14-invalid-date.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/analytics/recommendations?date=2024-6-15&limit=5" \
  "" "$p14_invalid_date_headers" "$p14_invalid_date_body" "$AUTH_HEADER"; then
  p14_invalid_date_status=$(http_status "$p14_invalid_date_headers")
  if [ "$p14_invalid_date_status" = "400" ]; then
    pass "P14 invalid date format returns 400"
  else
    fail "P14 invalid date format returned HTTP $p14_invalid_date_status instead of 400"
  fi
else
  fail "P14 invalid-date probe is unreachable"
fi

p14_invalid_limit_headers="$TMP_DIR/p14-invalid-limit.headers"
p14_invalid_limit_body="$TMP_DIR/p14-invalid-limit.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/analytics/recommendations?date=2024-06-15&limit=0" \
  "" "$p14_invalid_limit_headers" "$p14_invalid_limit_body" "$AUTH_HEADER"; then
  p14_invalid_limit_status=$(http_status "$p14_invalid_limit_headers")
  if [ "$p14_invalid_limit_status" = "400" ]; then
    pass "P14 invalid limit returns 400"
  else
    fail "P14 invalid limit returned HTTP $p14_invalid_limit_status instead of 400"
  fi
else
  fail "P14 invalid-limit probe is unreachable"
fi

section "Source Checks"
if grep -q "WINDOW_DAYS = 7" analytics-service/analytics_service/services/analytics.py \
  && grep -q "running_total" analytics-service/analytics_service/services/analytics.py \
  && grep -q "daily_counts.get" analytics-service/analytics_service/services/analytics.py; then
  pass "P11 peak-window implementation shows a fixed 7-day running window over day-by-day counts"
else
  fail "P11 peak-window implementation is missing expected running-window markers"
fi

if grep -q "_merge_sorted_feeds" rental-service/rental_service/services/rentals.py \
  && grep -q "_merge_feed_groups" rental-service/rental_service/services/rentals.py \
  && grep -q "left_index" rental-service/rental_service/services/rentals.py \
  && grep -q "right_index" rental-service/rental_service/services/rentals.py; then
  pass "P12 merged-feed implementation shows pairwise two-pointer merges across sorted streams"
else
  fail "P12 merged-feed implementation is missing expected merge markers"
fi

if grep -q "compute_surge_days" analytics-service/analytics_service/services/analytics.py \
  && grep -q "waiting_days" analytics-service/analytics_service/services/analytics.py \
  && grep -q "while waiting_days" analytics-service/analytics_service/services/analytics.py; then
  pass "P13 surge-days implementation shows a single-pass waiting-stack approach"
else
  fail "P13 surge-days implementation is missing expected single-pass markers"
fi

if grep -q "PAST_SEASONAL_YEARS = 2" analytics-service/analytics_service/services/analytics.py \
  && grep -q "/api/data/rentals" analytics-service/analytics_service/services/analytics.py \
  && grep -q "/api/data/products/batch" analytics-service/analytics_service/services/analytics.py; then
  pass "P14 recommendations implementation uses the two-year seasonal rental window plus batched product enrichment"
else
  fail "P14 recommendations implementation is missing expected seasonal-window markers"
fi

section "Summary"
printf 'PASS=%s FAIL=%s WARN=%s\n' "$PASS_COUNT" "$FAIL_COUNT" "$WARN_COUNT"
if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi
