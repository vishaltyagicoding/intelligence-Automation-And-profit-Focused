#!/bin/bash

echo "Setting up NeuralTrade..."

# Create .env from example if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please update with your credentials."
fi

# Create logs directory
mkdir -p logs

# Build and start containers
docker-compose up --build -d

echo "Setup complete! Access the platform at http://localhost"
echo "Admin panel: http://localhost/admin (admin/admin123)"
