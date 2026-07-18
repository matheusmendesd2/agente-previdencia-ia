#!/bin/bash
# Health check test for all services (3/3)
set -e

SERVICES=(
  "http://localhost:8000/health"
  "http://localhost:8080/health"
  "http://localhost:3000/health"
)
PASS=0
FAIL=0

for url in "${SERVICES[@]}"; do
  echo "Testing $url..."
  status=$(curl -s -o /tmp/hc.json -w "%{http_code}" "$url" 2>&1 || true)
  body=$(grep -o '"status"[[:space:]]*:[[:space:]]*"[^"]*"' /tmp/hc.json 2>/dev/null | grep -o '"[^"]*"$' | tr -d '"')
  if [ "$status" = "200" ] && [ "$body" = "ok" ]; then
    echo "  OK  $url -> $status ($body)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL $url -> $status (status=$body)"
    FAIL=$((FAIL + 1))
  fi
done

echo ""
echo "Results: $PASS passed, $FAIL failed"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
