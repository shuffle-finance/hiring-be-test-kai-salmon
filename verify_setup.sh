#!/bin/bash

# Backend Developer Coding Test - Setup Verification Script
# Run this script to verify that your test environment is properly configured

echo "🚀 Shuffle Finance Coding Test - Environment Verification"
echo "============================================================"
echo

# Check if Docker is running
echo "📦 Checking Docker..."
if ! docker ps >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi
echo "✅ Docker is running"

# Check if Docker Compose is available
echo "🔧 Checking Docker Compose..."
if ! docker compose version >/dev/null 2>&1; then
    echo "❌ Docker Compose is not available. Please install Docker Compose and try again."
    exit 1
fi
echo "✅ Docker Compose is available"

# Verify required files exist before starting
echo "📋 Verifying repository structure..."
REQUIRED_FILES=(
    "docker-compose.yml"
    "transaction-api/app.py"
    "transaction-api/Dockerfile"
    "transaction-api/requirements.txt"
    "database/init.sql"
    "data/transactions.json"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        MISSING_FILES+=("$file")
    fi
done

if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    echo "❌ Missing required files:"
    printf '   %s\n' "${MISSING_FILES[@]}"
    echo ""
    echo "💡 Make sure you're running this from the candidate repository root"
    echo "💡 Repository structure should include transaction-api/, database/, data/ directories"
    exit 1
fi
echo "✅ All required files present"

# Start the test environment
echo "🏗️  Starting test environment..."
if ! docker compose up -d; then
    echo "❌ Failed to start Docker environment"
    echo "💡 Check Docker logs: docker compose logs"
    exit 1
fi

# Wait a moment for services to start
echo "⏳ Waiting for services to start..."
sleep 5

# Check if transaction API is responding
echo "🔍 Checking transaction API..."
MAX_RETRIES=6
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s --fail http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ Transaction API is responding at http://localhost:8000"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "⏳ API not ready yet, retrying... ($RETRY_COUNT/$MAX_RETRIES)"
            sleep 5
        else
            echo "❌ Transaction API is not responding after $MAX_RETRIES attempts"
            echo "🔍 Checking container status..."
            docker compose ps
            echo ""
            echo "🔍 Transaction API logs:"
            docker compose logs transaction-api
            exit 1
        fi
    fi
done

# Check if PostgreSQL is available
echo "🗄️  Checking PostgreSQL database..."
if docker exec coding-test-postgres pg_isready -U test_user -d coding_test >/dev/null 2>&1; then
    echo "✅ PostgreSQL database is available"
else
    echo "❌ PostgreSQL database is not available. Checking logs..."
    docker compose logs postgres
    exit 1
fi

# Test API endpoints
echo "🌐 Testing API endpoints..."

# Test health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"' || echo "$HEALTH_RESPONSE" | grep -q '"status": "healthy"'; then
    echo "✅ Health endpoint working"
else
    echo "❌ Health endpoint not working properly"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi

# Test accounts endpoint
ACCOUNTS_RESPONSE=$(curl -s http://localhost:8000/accounts)
ACCOUNT_COUNT=$(echo "$ACCOUNTS_RESPONSE" | jq -r '.accounts | length' 2>/dev/null || echo "0")
if [ "$ACCOUNT_COUNT" -gt 0 ]; then
    echo "✅ Accounts endpoint working ($ACCOUNT_COUNT accounts available)"
else
    echo "❌ Accounts endpoint not working properly"
    echo "Response: $ACCOUNTS_RESPONSE"
    exit 1
fi

# Test stats endpoint
STATS_RESPONSE=$(curl -s http://localhost:8000/stats)
TRANSACTION_COUNT=$(echo "$STATS_RESPONSE" | jq -r '.total_transaction_records // .total_transactions // 0' 2>/dev/null || echo "0")
if [ "$TRANSACTION_COUNT" -gt 0 ] 2>/dev/null; then
    echo "✅ Stats endpoint working ($TRANSACTION_COUNT transaction records loaded)"
else
    echo "❌ Stats endpoint not working properly"
    echo "Response: $STATS_RESPONSE"
    exit 1
fi

echo
echo "🎉 SUCCESS! Your test environment is ready!"
echo "============================================"
echo
echo "📖 Next steps:"
echo "   1. Read CODING_TEST_BRIEFING.md for complete instructions"
echo "   2. Start building your solution in candidate-solution/"
echo "   3. Test your API endpoints when ready"
echo
echo "🔗 Available endpoints:"
echo "   • Transaction API: http://localhost:8000"
echo "   • PostgreSQL: localhost:5432 (db: coding_test, user: test_user, pass: test_password)"
echo
echo "📊 Quick API examples:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8000/accounts"
echo "   curl \"http://localhost:8000/accounts/$(echo "$ACCOUNTS_RESPONSE" | jq -r '.accounts[0]' 2>/dev/null)/transactions?limit=3\""
echo
echo "Good luck with your coding test! 🚀"
echo ""
echo "🚨 Important: Keep Docker running during your coding session!"
echo "🚨 If you need to restart: docker compose down && docker compose up -d" 