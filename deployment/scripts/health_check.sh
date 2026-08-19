#!/bin/bash
# Health check script

set -e

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:8501}"
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"

echo "🔍 Running health checks..."

# Check backend
echo -n "Backend API: "
if curl -sf "$BACKEND_URL/api/health" > /dev/null; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
    exit 1
fi

# Check frontend
echo -n "Frontend: "
if curl -sf "$FRONTEND_URL/_stcore/health" > /dev/null; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
    exit 1
fi

# Check Ollama
echo -n "Ollama: "
if curl -sf "$OLLAMA_URL/api/tags" > /dev/null; then
    echo "✅ Healthy"
else
    echo "⚠️  Unavailable (optional)"
fi

echo "✅ All critical services are healthy!"