# Persistent Command Context System

## 🧠 Smart Command Awareness

All commands automatically know your development environment state without you having to repeat it every time.

## 📋 Context File System

### Global Command Context
```bash
# Location: .claude/context/global-state.json
{
  "development": {
    "serverRunning": true,
    "serverCommand": "npm run dev",
    "autoRestart": true,
    "ports": {
      "api": 8084,
      "web": 3004,
      "database": 5434
    },
    "lastChecked": "2025-01-15T10:30:00Z"
  },
  "user": {
    "role": "admin",
    "preferences": {
      "noServerRestart": true,
      "autoDetectBuilding": true,
      "waitForBuildCompletion": true
    },
    "workingHours": "09:00-18:00"
  },
  "project": {
    "name": "TribeVibe",
    "framework": "React + Fastify",
    "buildSystem": "Vite",
    "testRunner": "Vitest"
  }
}
```

### Environment Rules
```bash
# Location: .claude/context/environment-rules.md

# 🎯 DEVELOPMENT ENVIRONMENT RULES

## Server Management
- **NEVER restart servers** - User runs `npm run dev` manually
- **Server auto-restarts** on code changes via Vite/Nodemon
- **Building detection** - Server may appear "down" during builds
- **Wait for builds** - Always wait 10-15s if build detected

## Port Usage
- API: 8084 (managed by npm run dev)
- Web: 3004 (managed by npm run dev)
- Database: 5434 (Docker container)
- **Check ports** before assuming services are down

## Build System
- Vite handles frontend builds automatically
- Node.js API restarts on file changes
- **Brief downtime** during builds is normal
- **Never manually restart** - let auto-restart handle it

## Testing
- Tests run independently of dev servers
- Safe to run tests while servers are running
- Database tests use separate test database (port 5435)
```

### Smart Context Loading in Every Command
```bash
# Add to beginning of every command

### Load Persistent Context (AUTOMATIC)
LOAD_COMMAND_CONTEXT() {
  local CONTEXT_FILE=".claude/context/global-state.json"
  local RULES_FILE=".claude/context/environment-rules.md"

  # Load global state
  if [[ -f "$CONTEXT_FILE" ]]; then
    SERVER_RUNNING=$(cat "$CONTEXT_FILE" | jq -r '.development.serverRunning // false' 2>/dev/null)
    AUTO_RESTART=$(cat "$CONTEXT_FILE" | jq -r '.development.autoRestart // true' 2>/dev/null)
    USER_ROLE=$(cat "$CONTEXT_FILE" | jq -r '.user.role // "developer"' 2>/dev/null)
    NO_SERVER_RESTART=$(cat "$CONTEXT_FILE" | jq -r '.user.preferences.noServerRestart // false' 2>/dev/null)

    echo "🧠 Context loaded: Server running=$SERVER_RUNNING, Auto-restart=$AUTO_RESTART, Role=$USER_ROLE"
  else
    echo "⚠️  No persistent context found - using defaults"
    SERVER_RUNNING=false
    AUTO_RESTART=true
    USER_ROLE="developer"
    NO_SERVER_RESTART=false
  fi

  # Update server status with real-time check
  UPDATE_SERVER_STATUS
}

### Real-time Server Status Check
UPDATE_SERVER_STATUS() {
  echo "🔍 Checking current server status..."

  # Check if API is responding
  if curl -s http://localhost:8084/health >/dev/null 2>&1; then
    API_RUNNING=true
    echo "  ✅ API server responding on port 8084"
  else
    API_RUNNING=false

    # Check if it's building
    if pgrep -f "vite\|webpack\|tsc.*watch" >/dev/null 2>&1; then
      echo "  🔄 Build process detected - API may be restarting"
      BUILDING=true

      if [[ "$AUTO_RESTART" == "true" ]]; then
        echo "  ⏳ Waiting 15s for build completion..."
        sleep 15

        # Check again after build wait
        if curl -s http://localhost:8084/health >/dev/null 2>&1; then
          API_RUNNING=true
          echo "  ✅ API server back online after build"
        else
          echo "  ⚠️  API still not responding after build wait"
        fi
      fi
    else
      echo "  ❌ API server not responding and no build process detected"
    fi
  fi

  # Check if Web is responding
  if curl -s http://localhost:3004 >/dev/null 2>&1; then
    WEB_RUNNING=true
    echo "  ✅ Web server responding on port 3004"
  else
    WEB_RUNNING=false
    echo "  ❌ Web server not responding on port 3004"
  fi

  # Update context file with current status
  UPDATE_CONTEXT_FILE
}

UPDATE_CONTEXT_FILE() {
  local CONTEXT_FILE=".claude/context/global-state.json"
  mkdir -p ".claude/context"

  # Update with current status
  cat > "$CONTEXT_FILE" << EOF
{
  "development": {
    "serverRunning": $API_RUNNING,
    "webServerRunning": $WEB_RUNNING,
    "serverCommand": "npm run dev",
    "autoRestart": $AUTO_RESTART,
    "building": ${BUILDING:-false},
    "ports": {
      "api": 8084,
      "web": 3004,
      "database": 5434
    },
    "lastChecked": "$(date -Iseconds)"
  },
  "user": {
    "role": "$USER_ROLE",
    "preferences": {
      "noServerRestart": $NO_SERVER_RESTART,
      "autoDetectBuilding": true,
      "waitForBuildCompletion": true
    }
  },
  "project": {
    "name": "TribeVibe",
    "framework": "React + Fastify",
    "buildSystem": "Vite",
    "testRunner": "Vitest"
  }
}
EOF
}

# Call at start of every command
LOAD_COMMAND_CONTEXT
```

## 🎯 Smart Server-Aware Behavior

### In Debug Command
```bash
### Server-Aware Debugging (ENHANCED)

if [[ "$API_RUNNING" == "false" && "$NO_SERVER_RESTART" == "true" ]]; then
  echo "⚠️  API server not responding, but user preference is NO auto-restart"
  echo "💡 Recommendation: Check 'npm run dev' output for errors"
  echo "⏳ Continuing with available diagnostics..."

  # Focus on system diagnostics instead of server requests
  FOCUS_SYSTEM_DIAGNOSTICS=true
else
  echo "✅ API server responding - proceeding with full diagnostics"
  FOCUS_SYSTEM_DIAGNOSTICS=false
fi
```

### In Test Commands
```bash
### Test-Aware Server State

if [[ "$SERVER_RUNNING" == "true" ]]; then
  echo "✅ Development servers running - tests will use test database"
  echo "🔒 Test isolation: Using port 5435 for test database"
  # Tests run independently
else
  echo "⚠️  Development servers not detected"
  if [[ "$NO_SERVER_RESTART" == "true" ]]; then
    echo "💡 User manages servers manually - running tests in isolation"
  fi
fi
```

### In Refactor Commands
```bash
### Build-Aware Refactoring

if [[ "$AUTO_RESTART" == "true" ]]; then
  echo "🔄 Auto-restart enabled - changes will trigger automatic rebuild"
  echo "💡 No manual server restart needed after refactoring"
  WAIT_FOR_RESTART=true
else
  echo "⚙️  Manual server management detected"
  WAIT_FOR_RESTART=false
fi
```

## 🛠️ Context Management Commands

### Update Context Command
```bash
# /update-context - Update persistent command context
echo "🔧 UPDATING COMMAND CONTEXT"
echo "==========================="

echo "Current server setup:"
echo "[Y/n] Are you running 'npm run dev' for development? "
read -r SERVER_MANAGED
if [[ "$SERVER_MANAGED" =~ ^[Yy]$ ]] || [[ -z "$SERVER_MANAGED" ]]; then
  NO_SERVER_RESTART=true
  AUTO_RESTART=true
else
  NO_SERVER_RESTART=false
  AUTO_RESTART=false
fi

echo "Context updated! All commands will now remember:"
echo "  → Server managed manually: $NO_SERVER_RESTART"
echo "  → Auto-restart enabled: $AUTO_RESTART"
echo "  → Role: admin"

UPDATE_CONTEXT_FILE
```

## 📊 Benefits

### For You (Admin)
- **Never repeat yourself** - Commands remember your setup
- **No accidental restarts** - Commands know you manage servers
- **Build-aware** - Commands wait for builds to complete
- **Smart diagnostics** - Focus on relevant issues for your setup

### For Commands
- **Consistent behavior** - All commands use same context
- **Intelligent decisions** - Server-aware routing and recommendations
- **Reduced errors** - No attempts to restart managed servers
- **Better UX** - Context-appropriate suggestions and actions

## 🔄 Command Tester Update

Yes, we should update the architecture tester to validate the context system:

```bash
# Test 7: Context System Validation
echo "🧠 TEST 7: Context System Validation"
echo "-----------------------------------"

if [[ -f ".claude/context/global-state.json" ]]; then
    echo "✅ Global context file found"
    SERVER_PREF=$(cat .claude/context/global-state.json | jq -r '.user.preferences.noServerRestart // false')
    echo "✅ Server restart preference: $SERVER_PREF"
else
    echo "❌ Global context file missing"
fi

if [[ -f ".claude/context/environment-rules.md" ]]; then
    echo "✅ Environment rules documentation present"
else
    echo "❌ Environment rules missing"
fi
```

This system gives you **persistent command intelligence** - every command automatically knows your development setup without you having to explain it repeatedly! 🧠✨