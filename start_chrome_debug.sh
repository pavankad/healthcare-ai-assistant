#!/bin/bash
# Script to start Chrome with remote debugging on macOS

echo "🌐 Starting Chrome with remote debugging..."

# Kill any existing Chrome processes (optional)
# killall "Google Chrome" 2>/dev/null

# Start Chrome with debugging port
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome_debug_session \
  "http://localhost:5000" &

echo "✅ Chrome started with debugging on port 9222"
echo "🔗 Navigate to: http://localhost:5000"
echo "🔐 Login with: admin/admin"
echo ""
echo "Then run: python connect_existing_browser.py"
