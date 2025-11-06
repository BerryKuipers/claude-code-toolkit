#!/usr/bin/env bash

# MCP Broker Setup Helper
# This script helps you configure the MCP broker for Claude Code

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   MCP Broker Setup Helper            ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
echo ""

# Detect script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BROKER_JS="$SCRIPT_DIR/dist/broker.js"

echo -e "${BLUE}📂 Detected broker location:${NC}"
echo "   $SCRIPT_DIR"
echo ""

# Check if already built
if [ ! -f "$BROKER_JS" ]; then
    echo -e "${YELLOW}⚠️  Broker not built yet${NC}"
    echo ""
    read -p "Would you like to build it now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}📦 Installing dependencies...${NC}"
        npm install
        echo ""
        echo -e "${BLUE}🔨 Building broker...${NC}"
        npm run build
        echo -e "${GREEN}✓ Build complete!${NC}"
        echo ""
    else
        echo -e "${RED}✗ Cannot continue without building. Run: npm install && npm run build${NC}"
        exit 1
    fi
fi

# Check for config files
if [ ! -f "$SCRIPT_DIR/servers.config.json" ]; then
    echo -e "${YELLOW}⚠️  servers.config.json not found${NC}"
    echo ""
    read -p "Would you like to create it from sample? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp "$SCRIPT_DIR/servers.config.sample.json" "$SCRIPT_DIR/servers.config.json"
        echo -e "${GREEN}✓ Created servers.config.json${NC}"
        echo -e "${YELLOW}  Edit this file to add your MCP servers${NC}"
        echo ""
    fi
fi

# Generate Claude Code config snippet
echo -e "${BLUE}📋 Claude Code Configuration:${NC}"
echo ""
echo "Add this to your .claude.json file:"
echo ""

# Detect OS and format path accordingly
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows (Git Bash)
    WINDOWS_PATH=$(cygpath -w "$BROKER_JS" | sed 's/\\/\\\\/g')
    echo -e "${GREEN}{"
    echo "  \"mcpServers\": {"
    echo "    \"broker\": {"
    echo "      \"command\": \"node\","
    echo "      \"args\": ["
    echo "        \"$WINDOWS_PATH\""
    echo "      ]"
    echo "    }"
    echo "  }"
    echo -e "}${NC}"
    echo ""
    echo -e "${BLUE}Location:${NC} C:\\Users\\YourUsername\\.claude.json"
else
    # Linux/Mac
    echo -e "${GREEN}{"
    echo "  \"mcpServers\": {"
    echo "    \"broker\": {"
    echo "      \"command\": \"node\","
    echo "      \"args\": ["
    echo "        \"$BROKER_JS\""
    echo "      ]"
    echo "    }"
    echo "  }"
    echo -e "}${NC}"
    echo ""
    echo -e "${BLUE}Location:${NC} ~/.claude.json"
fi

echo ""
echo -e "${BLUE}📖 Next Steps:${NC}"
echo ""
echo "1. Edit servers.config.json to add your MCP servers"
echo "2. Copy the configuration above to your .claude.json"
echo "3. Restart Claude Code"
echo "4. Use broker.search to discover available tools"
echo ""
echo -e "${GREEN}✓ Setup helper complete!${NC}"
echo ""
echo "For detailed documentation, see:"
echo "  - SETUP.md (comprehensive setup guide)"
echo "  - REFLECTIVE-MODE.md (dynamic tool discovery)"
echo "  - VAULT-SETUP.md (secure secret management)"
echo ""
