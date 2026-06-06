#!/bin/bash

# Pool Occupancy Tracker - Docker Runner Script

# Check for .env file (required for BOT_* environment variables)
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "   Create one from the template: cp .env.example .env"
    echo "   Then fill in your BOT_NAME, BOT_VERSION, BOT_URL, and BOT_EMAIL."
    exit 1
fi

echo "🏊 Pool Occupancy Tracker - Docker Setup"
echo "========================================"

echo "🚀 Available options:"
echo "1. Start services (build if needed):"
echo "   docker compose up -d --build"
echo ""
echo "2. Stop and remove services (cleanup):"
echo "   docker compose down"
echo ""
echo "3. Run occupancy tracker once:"
echo "   docker compose run --rm pool-tracker python occupancy.py"
echo ""
echo "4. Run aggregation once:"
echo "   docker compose run --rm pool-tracker python -m pool_aggregation"
echo ""
echo "5. Run capacity tracker once:"
echo "   docker compose run --rm pool-tracker python capacity.py"
echo ""
echo "6. Interactive shell in container:"
echo "   docker compose run --rm pool-tracker bash"
echo ""
echo "7. View service logs:"
echo "   docker compose logs -f"
echo ""

# Ask user what they want to do
read -p "What would you like to do? (1/2/3/4/5/6/7): " choice

case $choice in
    1)
        echo "🔄 Starting services with Docker Compose (building if needed)..."
        docker compose up -d --build
        if [ $? -eq 0 ]; then
            echo "✅ Services started! Check logs with: docker compose logs -f"
        else
            echo "❌ Failed to start services!"
        fi
        ;;
    2)
        echo "🧹 Stopping and removing services..."
        docker compose down
        if [ $? -eq 0 ]; then
            echo "✅ Services stopped and removed successfully!"
        else
            echo "❌ Failed to stop and remove services!"
        fi
        ;;
    3)
        echo "🏃 Running occupancy tracker once..."
        docker compose run --rm pool-tracker python occupancy.py
        ;;
    4)
        echo "📊 Running aggregation once..."
        docker compose run --rm pool-tracker python -m pool_aggregation
        ;;
    5)
        echo "📊 Running capacity tracker once..."
        docker compose run --rm pool-tracker python capacity.py
        ;;
    6)
        echo "🐚 Starting interactive shell..."
        docker compose run --rm pool-tracker bash
        ;;
    7)
        echo "📋 Showing service logs (Press Ctrl+C to exit)..."
        docker compose logs -f
        ;;
    *)
        echo "ℹ️  No option selected. You can run the commands manually."
        ;;
esac