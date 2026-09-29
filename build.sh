#!/usr/bin/env bash
# Lucen AI — Render Build Script
# Builds the frontend and installs backend dependencies
set -euo pipefail

echo "=== Lucen AI Build ==="

# 1. Install Python dependencies
echo "→ Installing Python dependencies..."
pip install -r requirements.txt

# 2. Build frontend
echo "→ Installing frontend dependencies..."
cd frontend
npm ci
echo "→ Building frontend..."
npm run build
cd ..

echo "→ Build complete!"
