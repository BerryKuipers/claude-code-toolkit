#!/bin/bash
set -e

# Default values
PUID=${PUID:-1000}
PGID=${PGID:-1000}
UMASK=${UMASK:-022}

echo "🐳 Starting Crypto Portfolio Dashboard..."
echo "📋 User ID: $PUID"
echo "📋 Group ID: $PGID"
echo "📋 UMASK: $UMASK"

# Create group if it doesn't exist
if ! getent group $PGID > /dev/null 2>&1; then
    echo "📝 Creating group with GID $PGID"
    groupadd -g $PGID appgroup
else
    echo "📝 Using existing group with GID $PGID"
fi

# Create user if it doesn't exist
if ! getent passwd $PUID > /dev/null 2>&1; then
    echo "📝 Creating user with UID $PUID"
    useradd -u $PUID -g $PGID -d /app -s /bin/bash appuser
else
    echo "📝 Using existing user with UID $PUID"
fi

# Set UMASK
umask $UMASK

# Ensure directories exist and have correct permissions
echo "📁 Setting up directories..."
mkdir -p /app/logs /app/data /app/config

# Change ownership of app directory and subdirectories
echo "🔧 Setting permissions..."
chown -R $PUID:$PGID /app

# Test write permissions
echo "🧪 Testing write permissions..."
if gosu $PUID:$PGID touch /app/logs/test.log 2>/dev/null; then
    echo "✅ Write permissions OK"
    rm -f /app/logs/test.log
else
    echo "⚠️  Warning: Limited write permissions to logs directory"
fi

echo "🚀 Starting application as UID:$PUID GID:$PGID..."

# Execute the command as the specified user
exec gosu $PUID:$PGID "$@"
