#!/bin/sh
set -eu

COMPOSE_CMD=${COMPOSE_CMD:-"docker compose -f docker-compose.yml"}
BASE_URL=${BASE_URL:-"http://localhost:8000"}
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

  if [ -n "$body" ]; then
    curl -sS -X "$method" "$url" \
      -H "Content-Type: application/json" \
      -D "$headers_file" \
      -o "$body_file" \
      --data "$body"
  else
    curl -sS -X "$method" "$url" \
      -D "$headers_file" \
      -o "$body_file"
  fi
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

need_cmd curl
need_cmd docker
need_cmd python3

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

section "P1 Health Checks"
gateway_headers="$TMP_DIR/gateway-status.headers"
gateway_body="$TMP_DIR/gateway-status.json"
if http_request GET "$BASE_URL/status" "" "$gateway_headers" "$gateway_body"; then
  gateway_status=$(http_status "$gateway_headers")
  if [ "$gateway_status" = "200" ]; then
    pass "gateway /status returned HTTP 200"
  else
    fail "gateway /status returned HTTP $gateway_status"
  fi

  if json_value_equals "$gateway_body" "service" "api-gateway"; then
    pass "gateway /status reports service=api-gateway"
  else
    fail "gateway /status service field is incorrect"
  fi

  for key in user-service rental-service analytics-service agentic-service; do
    if json_has_key "$gateway_body" "downstream.$key"; then
      pass "gateway /status includes downstream.$key"
    else
      fail "gateway /status missing downstream.$key"
    fi
  done
else
  fail "gateway /status is unreachable"
fi

for service_port in 8001 8002 8003 8004; do
  service_headers="$TMP_DIR/service-${service_port}.headers"
  service_body="$TMP_DIR/service-${service_port}.json"
  service_name=$(case "$service_port" in
    8001) printf 'user-service' ;;
    8002) printf 'rental-service' ;;
    8003) printf 'analytics-service' ;;
    8004) printf 'agentic-service' ;;
  esac)
  if http_request GET "http://localhost:${service_port}/status" "" "$service_headers" "$service_body"; then
    service_status=$(http_status "$service_headers")
    fail "${service_name} is publicly reachable on localhost:${service_port} (HTTP $service_status); only gateway should be exposed"
  else
    pass "${service_name} direct HTTP /status is not publicly reachable on localhost:${service_port}"
  fi
done

section "P2 User Authentication"
register_name_headers="$TMP_DIR/register-name.headers"
register_name_body="$TMP_DIR/register-name.json"
register_name_email="chapter1-name-${RUN_ID}@example.com"
register_name_payload=$(printf '{"name":"Chapter One User","email":"%s","password":"password123"}' "$register_name_email")
if http_request POST "$BASE_URL/users/register" "$register_name_payload" "$register_name_headers" "$register_name_body"; then
  register_name_status=$(http_status "$register_name_headers")
  if [ "$register_name_status" = "201" ] || [ "$register_name_status" = "200" ]; then
    pass "register works with README payload shape {name,email,password}"
  else
    fail "register with README payload shape returned HTTP $register_name_status"
  fi
else
  fail "register with README payload shape is unreachable"
fi

register_headers="$TMP_DIR/register.headers"
register_body="$TMP_DIR/register.json"
register_email="chapter1-${RUN_ID}@example.com"
register_payload=$(printf '{"full_name":"Chapter One User","email":"%s","password":"password123"}' "$register_email")
TOKEN=""
if http_request POST "$BASE_URL/users/register" "$register_payload" "$register_headers" "$register_body"; then
  register_status=$(http_status "$register_headers")
  if [ "$register_status" = "201" ] || [ "$register_status" = "200" ]; then
    if json_has_key "$register_body" "access_token"; then
      pass "register returns an access_token"
      TOKEN=$(extract_json_value "$register_body" "access_token")
    else
      fail "register response missing access_token"
    fi
  else
    fail "register with implementation payload returned HTTP $register_status"
  fi
else
  fail "register with implementation payload is unreachable"
fi

duplicate_headers="$TMP_DIR/register-duplicate.headers"
duplicate_body="$TMP_DIR/register-duplicate.json"
if http_request POST "$BASE_URL/users/register" "$register_payload" "$duplicate_headers" "$duplicate_body"; then
  duplicate_status=$(http_status "$duplicate_headers")
  if [ "$duplicate_status" = "409" ]; then
    pass "duplicate register returns 409"
  else
    fail "duplicate register returned HTTP $duplicate_status instead of 409"
  fi
else
  fail "duplicate register request failed unexpectedly"
fi

login_headers="$TMP_DIR/login.headers"
login_body="$TMP_DIR/login.json"
login_payload=$(printf '{"email":"%s","password":"password123"}' "$register_email")
if http_request POST "$BASE_URL/users/login" "$login_payload" "$login_headers" "$login_body"; then
  login_status=$(http_status "$login_headers")
  if [ "$login_status" = "200" ] && json_has_key "$login_body" "access_token"; then
    pass "login returns an access_token"
    TOKEN=$(extract_json_value "$login_body" "access_token")
  else
    fail "login did not return the expected token payload"
  fi
else
  fail "login request is unreachable"
fi

wrong_login_headers="$TMP_DIR/login-wrong.headers"
wrong_login_body="$TMP_DIR/login-wrong.json"
wrong_login_payload=$(printf '{"email":"%s","password":"wrongpass123"}' "$register_email")
if http_request POST "$BASE_URL/users/login" "$wrong_login_payload" "$wrong_login_headers" "$wrong_login_body"; then
  wrong_login_status=$(http_status "$wrong_login_headers")
  if [ "$wrong_login_status" = "401" ]; then
    pass "invalid login returns 401"
  else
    fail "invalid login returned HTTP $wrong_login_status instead of 401"
  fi
else
  fail "invalid login request failed unexpectedly"
fi

me_headers="$TMP_DIR/me.headers"
me_body="$TMP_DIR/me.json"
if [ -n "$TOKEN" ]; then
  if curl -sS "$BASE_URL/users/me" \
    -H "Authorization: Bearer $TOKEN" \
    -D "$me_headers" \
    -o "$me_body"; then
    me_status=$(http_status "$me_headers")
    if [ "$me_status" = "200" ] && json_has_key "$me_body" "email"; then
      pass "authenticated /users/me returns the user profile"
    else
      fail "authenticated /users/me returned HTTP $me_status"
    fi
  else
    fail "authenticated /users/me is unreachable"
  fi
else
  fail "skipping /users/me because no JWT was obtained"
fi

section "P3 Product Proxy"
products_headers="$TMP_DIR/products.headers"
products_body="$TMP_DIR/products.json"
if [ -n "$TOKEN" ]; then
  if curl -sS "$BASE_URL/rentals/products" \
    -H "Authorization: Bearer $TOKEN" \
    -D "$products_headers" \
    -o "$products_body"; then
    products_status=$(http_status "$products_headers")
    if [ "$products_status" = "200" ]; then
      if json_has_key "$products_body" "data"; then
        pass "/rentals/products returns a data envelope"
      else
        fail "/rentals/products response is missing the data field"
      fi
    else
      fail "/rentals/products returned HTTP $products_status"
    fi
  else
    fail "/rentals/products is unreachable"
  fi
else
  fail "skipping /rentals/products because no JWT was obtained"
fi

filtered_headers="$TMP_DIR/products-filtered.headers"
filtered_body="$TMP_DIR/products-filtered.json"
if [ -n "$TOKEN" ]; then
  if curl -sS "$BASE_URL/rentals/products?category=TOOLS&page=1&limit=2&owner_id=1" \
    -H "Authorization: Bearer $TOKEN" \
    -D "$filtered_headers" \
    -o "$filtered_body"; then
    filtered_status=$(http_status "$filtered_headers")
    if [ "$filtered_status" = "200" ]; then
      pass "/rentals/products forwards query parameters without crashing"
    else
      fail "/rentals/products with forwarded query params returned HTTP $filtered_status"
    fi
  else
    fail "/rentals/products with forwarded query params is unreachable"
  fi
else
  fail "skipping filtered /rentals/products because no JWT was obtained"
fi

product_headers="$TMP_DIR/product.headers"
product_body="$TMP_DIR/product.json"
if [ -n "$TOKEN" ]; then
  if curl -sS "$BASE_URL/rentals/products/1" \
    -H "Authorization: Bearer $TOKEN" \
    -D "$product_headers" \
    -o "$product_body"; then
    product_status=$(http_status "$product_headers")
    if [ "$product_status" = "200" ]; then
      pass "/rentals/products/:id returns HTTP 200 for a sample product"
    else
      fail "/rentals/products/1 returned HTTP $product_status"
    fi
  else
    fail "/rentals/products/1 is unreachable"
  fi
else
  fail "skipping /rentals/products/1 because no JWT was obtained"
fi

missing_headers="$TMP_DIR/product-missing.headers"
missing_body="$TMP_DIR/product-missing.json"
if [ -n "$TOKEN" ]; then
  if curl -sS "$BASE_URL/rentals/products/999999999" \
    -H "Authorization: Bearer $TOKEN" \
    -D "$missing_headers" \
    -o "$missing_body"; then
    missing_status=$(http_status "$missing_headers")
    if [ "$missing_status" = "404" ] || [ "$missing_status" = "429" ] || [ "$missing_status" = "502" ]; then
      warn "/rentals/products missing-product probe returned HTTP $missing_status; inspect whether error mapping matches README expectations"
    else
      warn "/rentals/products missing-product probe returned HTTP $missing_status"
    fi
  else
    warn "/rentals/products missing-product probe could not be completed"
  fi
else
  warn "skipping missing-product probe because no JWT was obtained"
fi

section "P4 Docker Compose and Builds"
compose_ps_file="$TMP_DIR/compose-ps.txt"
if $COMPOSE_CMD ps >"$compose_ps_file"; then
  if grep -q "healthy" "$compose_ps_file"; then
    pass "at least one compose service reports healthy"
  else
    warn "compose ps does not currently show healthy services"
  fi
else
  fail "docker compose ps failed during verification"
fi

config_file="$TMP_DIR/compose-config.txt"
$COMPOSE_CMD config >"$config_file"
if grep -q "/status" "$config_file"; then
  pass "compose configuration references /status in at least one healthcheck"
else
  fail "compose healthchecks do not reference /status"
fi

has_postgres_volume=0
has_agent_store_volume=0

if grep -q "postgres_data" "$config_file"; then
  has_postgres_volume=1
fi

if grep -q "redis_data" "$config_file" || grep -q "mongo_data" "$config_file"; then
  has_agent_store_volume=1
fi

if [ "$has_postgres_volume" -eq 1 ] && [ "$has_agent_store_volume" -eq 1 ]; then
  pass "named volumes for postgres and agent store are configured"
else
  fail "named volumes for postgres and the configured agent store are missing from compose config"
fi

for dockerfile in \
  "user-service/Dockerfile" \
  "rental-service/Dockerfile" \
  "analytics-service/Dockerfile" \
  "agentic-service/Dockerfile" \
  "api-gateway/Dockerfile" \
  "frontend/Dockerfile"
do
  if grep -q "^FROM .* AS builder" "$dockerfile" && grep -q "^FROM .* AS " "$dockerfile"; then
    pass "${dockerfile} uses a multi-stage build"
  else
    fail "${dockerfile} does not appear to use the expected multi-stage pattern"
  fi
done

section "Summary"
printf 'Passed: %s\n' "$PASS_COUNT"
printf 'Failed: %s\n' "$FAIL_COUNT"
printf 'Warnings: %s\n' "$WARN_COUNT"

if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi
