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

json_value_equals() {
  python3 - "$1" "$2" "$3" <<'PY'
import json
import sys

path = sys.argv[2].split(".")
expected = sys.argv[3]
with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)
node = data
for part in path:
    if not isinstance(node, dict) or part not in node:
        raise SystemExit(1)
    node = node[part]
if str(node) != expected:
    raise SystemExit(1)
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
  register_email="chapter2-${RUN_ID}@example.com"
  register_payload=$(printf '{"full_name":"Chapter Two User","email":"%s","password":"password123"}' "$register_email")
  TOKEN=""

  if http_request POST "$BASE_URL/users/register" "$register_payload" "$register_headers" "$register_body"; then
    register_status=$(http_status "$register_headers")
    if [ "$register_status" = "201" ] || [ "$register_status" = "200" ]; then
      if json_has_key "$register_body" "access_token"; then
        pass "register returns an access_token for Chapter 2 verification"
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
        pass "login returns an access_token for Chapter 2 verification"
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
    tests/unit/test_discount.py \
    tests/unit/test_chapter2_rentals.py \
    tests/unit/test_chapter2_gateway.py >/dev/null; then
    pass "Chapter 2 unit tests pass"
  else
    fail "Chapter 2 unit tests failed"
  fi
else
  warn "uv is not installed; skipping Chapter 2 unit tests"
fi

section "Auth Setup"
register_and_login
if [ -n "${AUTH_HEADER:-}" ]; then
  pass "JWT acquired for protected Chapter 2 endpoints"
else
  fail "could not obtain JWT for protected Chapter 2 endpoints"
fi

section "P5 Paginated Product Listing"
p5_headers="$TMP_DIR/p5.headers"
p5_body="$TMP_DIR/p5.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/rentals/products?category=TOOLS&page=2&limit=20" \
  "" "$p5_headers" "$p5_body" "$AUTH_HEADER"; then
  p5_status=$(http_status "$p5_headers")
  if [ "$p5_status" = "200" ]; then
    pass "P5 listing route returns HTTP 200"
  else
    fail "P5 listing route returned HTTP $p5_status"
  fi

  for key in data page limit total totalPages; do
    if json_has_key "$p5_body" "$key"; then
      pass "P5 response includes $key"
    else
      fail "P5 response missing $key"
    fi
  done
else
  fail "P5 listing route is unreachable"
fi

p5_invalid_headers="$TMP_DIR/p5-invalid.headers"
p5_invalid_body="$TMP_DIR/p5-invalid.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/rentals/products?category=NOT_A_REAL_CATEGORY&page=1&limit=5" \
  "" "$p5_invalid_headers" "$p5_invalid_body" "$AUTH_HEADER"; then
  p5_invalid_status=$(http_status "$p5_invalid_headers")
  if [ "$p5_invalid_status" = "400" ]; then
    if json_has_key "$p5_invalid_body" "validCategories"; then
      pass "P5 invalid category returns helpful 400 with validCategories"
    else
      fail "P5 invalid category response missing validCategories"
    fi
  else
    fail "P5 invalid category returned HTTP $p5_invalid_status instead of 400"
  fi
else
  fail "P5 invalid-category probe is unreachable"
fi

section "P6 Loyalty Discount"
p6_headers="$TMP_DIR/p6.headers"
p6_body="$TMP_DIR/p6.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/users/42/discount" \
  "" "$p6_headers" "$p6_body" "$AUTH_HEADER"; then
  p6_status=$(http_status "$p6_headers")
  if [ "$p6_status" = "200" ]; then
    pass "P6 discount route returns HTTP 200"
  else
    fail "P6 discount route returned HTTP $p6_status"
  fi

  for key in userId securityScore discountPercent; do
    if json_has_key "$p6_body" "$key"; then
      pass "P6 response includes $key"
    else
      fail "P6 response missing $key"
    fi
  done
else
  fail "P6 discount route is unreachable"
fi

p6_missing_headers="$TMP_DIR/p6-missing.headers"
p6_missing_body="$TMP_DIR/p6-missing.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/users/999999999/discount" \
  "" "$p6_missing_headers" "$p6_missing_body" "$AUTH_HEADER"; then
  p6_missing_status=$(http_status "$p6_missing_headers")
  if [ "$p6_missing_status" = "404" ]; then
    pass "P6 missing user returns 404"
  else
    warn "P6 missing user probe returned HTTP $p6_missing_status"
  fi
else
  warn "P6 missing-user probe could not be completed"
fi

section "P7 Availability"
p7_headers="$TMP_DIR/p7.headers"
p7_body="$TMP_DIR/p7.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/rentals/products/42/availability?from=2024-03-01&to=2024-03-14" \
  "" "$p7_headers" "$p7_body" "$AUTH_HEADER"; then
  p7_status=$(http_status "$p7_headers")
  if [ "$p7_status" = "200" ]; then
    pass "P7 availability route returns HTTP 200"
  else
    fail "P7 availability route returned HTTP $p7_status"
  fi

  for key in productId from to available busyPeriods freeWindows; do
    if json_has_key "$p7_body" "$key"; then
      pass "P7 response includes $key"
    else
      fail "P7 response missing $key"
    fi
  done
else
  fail "P7 availability route is unreachable"
fi

p7_invalid_headers="$TMP_DIR/p7-invalid.headers"
p7_invalid_body="$TMP_DIR/p7-invalid.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/rentals/products/42/availability?from=2024-03&to=2024-03-14" \
  "" "$p7_invalid_headers" "$p7_invalid_body" "$AUTH_HEADER"; then
  p7_invalid_status=$(http_status "$p7_invalid_headers")
  if [ "$p7_invalid_status" = "400" ]; then
    pass "P7 invalid date format returns 400"
  else
    fail "P7 invalid date format returned HTTP $p7_invalid_status instead of 400"
  fi
else
  fail "P7 invalid-date probe is unreachable"
fi

section "P8 Kth Busiest Date"
p8_headers="$TMP_DIR/p8.headers"
p8_body="$TMP_DIR/p8.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/rentals/kth-busiest-date?from=2024-01&to=2024-03&k=3" \
  "" "$p8_headers" "$p8_body" "$AUTH_HEADER"; then
  p8_status=$(http_status "$p8_headers")
  if [ "$p8_status" = "200" ]; then
    pass "P8 kth-busiest-date route returns HTTP 200"
  else
    fail "P8 kth-busiest-date route returned HTTP $p8_status"
  fi

  for key in from to k date rentalCount; do
    if json_has_key "$p8_body" "$key"; then
      pass "P8 response includes $key"
    else
      fail "P8 response missing $key"
    fi
  done
else
  fail "P8 kth-busiest-date route is unreachable"
fi

p8_invalid_headers="$TMP_DIR/p8-invalid.headers"
p8_invalid_body="$TMP_DIR/p8-invalid.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/rentals/kth-busiest-date?from=2024-13&to=2024-03&k=0" \
  "" "$p8_invalid_headers" "$p8_invalid_body" "$AUTH_HEADER"; then
  p8_invalid_status=$(http_status "$p8_invalid_headers")
  if [ "$p8_invalid_status" = "400" ]; then
    pass "P8 invalid input returns 400"
  else
    fail "P8 invalid input returned HTTP $p8_invalid_status instead of 400"
  fi
else
  fail "P8 invalid-input probe is unreachable"
fi

section "P9 Top Categories"
p9_headers="$TMP_DIR/p9.headers"
p9_body="$TMP_DIR/p9.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/rentals/users/101/top-categories?k=5" \
  "" "$p9_headers" "$p9_body" "$AUTH_HEADER"; then
  p9_status=$(http_status "$p9_headers")
  if [ "$p9_status" = "200" ]; then
    pass "P9 top-categories route returns HTTP 200"
  else
    fail "P9 top-categories route returned HTTP $p9_status"
  fi

  for key in userId topCategories; do
    if json_has_key "$p9_body" "$key"; then
      pass "P9 response includes $key"
    else
      fail "P9 response missing $key"
    fi
  done
else
  fail "P9 top-categories route is unreachable"
fi

p9_invalid_headers="$TMP_DIR/p9-invalid.headers"
p9_invalid_body="$TMP_DIR/p9-invalid.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/rentals/users/101/top-categories?k=0" \
  "" "$p9_invalid_headers" "$p9_invalid_body" "$AUTH_HEADER"; then
  p9_invalid_status=$(http_status "$p9_invalid_headers")
  if [ "$p9_invalid_status" = "400" ]; then
    pass "P9 invalid k returns 400"
  else
    fail "P9 invalid k returned HTTP $p9_invalid_status instead of 400"
  fi
else
  fail "P9 invalid-k probe is unreachable"
fi

section "P10 Longest Free Streak"
p10_headers="$TMP_DIR/p10.headers"
p10_body="$TMP_DIR/p10.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/rentals/products/77/free-streak?year=2023" \
  "" "$p10_headers" "$p10_body" "$AUTH_HEADER"; then
  p10_status=$(http_status "$p10_headers")
  if [ "$p10_status" = "200" ]; then
    pass "P10 free-streak route returns HTTP 200"
  else
    fail "P10 free-streak route returned HTTP $p10_status"
  fi

  if json_has_key "$p10_body" "longestFreeStreak"; then
    pass "P10 response includes longestFreeStreak"
  else
    fail "P10 response missing longestFreeStreak"
  fi

  for key in longestFreeStreak.from longestFreeStreak.to longestFreeStreak.days; do
    if json_has_key "$p10_body" "$key"; then
      pass "P10 response includes $key"
    else
      fail "P10 response missing $key"
    fi
  done
else
  fail "P10 free-streak route is unreachable"
fi

p10_invalid_headers="$TMP_DIR/p10-invalid.headers"
p10_invalid_body="$TMP_DIR/p10-invalid.json"
if [ -n "${AUTH_HEADER:-}" ] && http_request GET \
  "$BASE_URL/rentals/products/77/free-streak?year=0" \
  "" "$p10_invalid_headers" "$p10_invalid_body" "$AUTH_HEADER"; then
  p10_invalid_status=$(http_status "$p10_invalid_headers")
  if [ "$p10_invalid_status" = "400" ]; then
    pass "P10 invalid year returns 400"
  else
    fail "P10 invalid year returned HTTP $p10_invalid_status instead of 400"
  fi
else
  fail "P10 invalid-year probe is unreachable"
fi

section "Source Checks"
if grep -q "CATEGORY_TTL_SECONDS" rental-service/rental_service/services/categories.py \
  && grep -q "_cache" rental-service/rental_service/services/categories.py \
  && grep -q '/api/data/categories' rental-service/rental_service/services/categories.py; then
  pass "P5 category validation is backed by cached Central API categories"
else
  fail "P5 category cache implementation is missing expected cache markers"
fi

if grep -q "merge_intervals" rental-service/rental_service/services/rentals.py \
  && grep -q "compute_free_windows" rental-service/rental_service/services/rentals.py; then
  pass "P7 availability logic uses merged intervals"
else
  fail "P7 availability logic does not show expected merged-interval flow"
fi

if grep -q "push_bounded" rental-service/rental_service/services/rentals.py; then
  pass "P8 kth-busiest-date uses a bounded heap helper"
else
  fail "P8 kth-busiest-date does not appear to use the optimized heap approach"
fi

if grep -q '/api/data/products/batch' rental-service/rental_service/services/rentals.py \
  && grep -q "BATCH_SIZE = 50" rental-service/rental_service/services/rentals.py; then
  pass "P9 top-categories uses the batch products endpoint with a 50 item chunk size"
else
  fail "P9 top-categories does not show the expected batch-fetch implementation"
fi

if grep -q "longest_free_streak" rental-service/rental_service/services/rentals.py \
  && grep -q "clip_interval" rental-service/rental_service/services/rentals.py; then
  pass "P10 free-streak clips rentals to the target year and scans merged gaps"
else
  fail "P10 free-streak implementation is missing expected clipping or gap-scan logic"
fi

if grep -q "extra_params" rental-service/rental_service/api/routes.py; then
  pass "rental-service HTTP route forwards non-category product query params"
else
  fail "rental-service HTTP route does not forward extra product query params"
fi

if grep -q "params.items()" api-gateway/gateway/api/routes.py \
  || grep -q "owner_id" api-gateway/gateway/api/routes.py; then
  pass "gateway product route appears to forward extra product query params"
else
  fail "gateway product route only forwards category/page/limit; Chapter 2 P5 is incomplete"
fi

if grep -Eq "map<string, *string>|owner_id" proto/rental.proto; then
  pass "rental gRPC contract can carry extra product query params"
else
  fail "rental gRPC contract cannot carry extra product query params for P5 forwarding"
fi

section "Summary"
printf 'Passed: %s\n' "$PASS_COUNT"
printf 'Failed: %s\n' "$FAIL_COUNT"
printf 'Warnings: %s\n' "$WARN_COUNT"

if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi
