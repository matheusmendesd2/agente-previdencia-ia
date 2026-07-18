#!/bin/bash
# Health check test for all services
set -e

SERVICES=(
  "http://localhost:8000/health"
  "http://localhost:5000/health"
  "http://localhost:3000/health"
)

PASS=0
FAIL=0

for url in "${SERVICES[@]}"; do
  echo "Testing $url..."
  status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1 || true)
  if [ "$status" = "200" ]; then
    echo "  ✓ $url -> $status"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $url -> $status (expected 200)"
    FAIL=$((FAIL + 1))
  fi
done

echo ""
echo "Results: $PASS passed, $FAIL failed"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
