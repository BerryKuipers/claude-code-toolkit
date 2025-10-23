# Slash Command Best Practices & Architecture

**Comprehensive guidelines for building maintainable, efficient slash commands in the TribeVibe project.**

## 🏗️ Core Architecture Principles

### **Separation of Concerns (SOC)**
Each command should have a **single, well-defined responsibility**:

- **data-setup**: Pure API validation only - checks user existence, never creates data
- **test-ui**: Pure browser/UI execution - handles ALL user interactions via UI
- **orchestrator**: Task routing and coordination, provides complete context to commands
- **app-discovery**: Application structure analysis from running services, never manages infrastructure
- **architect**: Code/design review, no data manipulation

### **NEW: Option A Pure Validation Architecture**
**Critical change**: Commands now follow pure validation approach:
- **data-setup**: Only validates (returns `needsRegistration: true/false`)
- **test-ui**: Handles registration, login, matching, messaging via UI
- **No API data creation**: All data flows through UI interactions

### **Chrome DevTools MCP Integration**
**Browser automation using Claude Code's Chrome MCP**: [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp)
- **Use hyphens**: `mcp__chrome-devtools__*` (NOT underscores `mcp__chrome_devtools__*`)
- **Functions**: `list_pages`, `navigate_page`, `take_screenshot`, `click`, `fill`, `take_snapshot`
- **Auto-managed**: Chrome instance handled by Claude Code, no manual setup required

### **Command Delegation Pattern**
```bash
# ✅ CORRECT: Complex tasks delegate through orchestrator
/orchestrator task="test message delete functionality"
# → Orchestrator delegates to: data-setup → app-discovery → test-ui

# ❌ WRONG: Commands trying to do everything
/test-ui task="create users, create match, then test delete"
```

### **Clean Input/Output Interface**
```markdown
## Command Template
**Arguments**: Clear parameter specification
**Success Criteria**: Specific, measurable outcomes
**Description**: Single sentence describing purpose
```

## 🚨 Critical Implementation Rules

### **1. NO External Script Creation**
```bash
# ❌ FORBIDDEN
echo "const api = ..." > scripts/new-file.js
node scripts/new-file.js

# ✅ CORRECT
node -e "fetch('http://localhost:8084/api/endpoint',{method:'POST',body:JSON.stringify(data)}).then(r=>r.json()).then(console.log)"
```

### **2. Single-Line Commands Only**
```bash
# ❌ FORBIDDEN: Multi-line in bash strings
node -e "
const data = {
  user: 'test'
};
fetch('/api', {body: data})
"

# ✅ CORRECT: Single line, no line breaks
node -e "fetch('/api',{method:'POST',body:JSON.stringify({user:'test'})}).then(r=>console.log(r.status))"
```

### **3. NO Emoji in Bash Strings**
```bash
# ❌ FORBIDDEN: Emoji causes bash syntax errors
echo "Creating user 👤 with data..."

# ✅ CORRECT: Plain text only
echo "Creating user with data..."
```

### **4. Accurate Status Reporting**
```bash
# ❌ FORBIDDEN: False positives
echo "✅ Task Complete" # when steps actually failed

# ✅ REQUIRED: Report actual results
if [ $exit_code -eq 0 ]; then
  echo "✅ Task Complete"
else
  echo "❌ Task Failed: $error_message"
fi
```

### **5. Chrome Profile Consistency**
```bash
# ✅ REQUIRED: Use user's remote debugging Chrome
--remote-debugging-port=9222 --user-data-dir=C:\temp\chrome-debug

# ❌ FORBIDDEN: MCP's default profile
C:\Users\BerryLocal\.cache\chrome-devtools-mcp\chrome-profile
```

### **6. 🚨 CRITICAL: SERVER_MANAGED_BY_USER Compliance**
```bash
# ✅ REQUIRED: Connect to existing services
const apiCheck = await fetch('http://localhost:8084/health');
const frontendCheck = await fetch('http://localhost:3004');

# ❌ FORBIDDEN: Any server management
npm run dev
node scripts/start-system.js
taskkill /PID <any-pid>
docker-compose up
pm2 start/stop/restart

# ✅ REQUIRED: Log violations immediately
logger.violation('SERVER_MANAGED_BY_USER', 'attempted npm run dev', 'critical');
```

**Why this matters**: Commands must work with user-controlled environment, never manage infrastructure.

## 📋 Command Workflow Patterns

### **UI Testing Workflow (NEW: Mandatory 3-Step)**
```bash
# Step 1: Validate test users (no creation)
/data-setup
# Returns: {"ok": true, "users": [{"name":"TestMale","needsRegistration":false}, ...]}

# Step 2: Discover app structure from running services
/app-discovery "discover all application patterns --type=all --output=json"
# Returns: {"routes": {...}, "endpoints": {...}, "selectors": {...}}

# Step 3: Execute UI testing with complete context
/test-ui {users: [...], routes: {...}, selectors: {...}, task: "test message delete functionality"}
# test-ui handles: registration → login → matching → messaging → deletion testing
```

### **KEY CHANGES from Old 4-Step Workflow:**
- ❌ **Removed**: API data creation step
- ❌ **Removed**: JWT token generation
- ✅ **Added**: Pure validation approach
- ✅ **Added**: Complete UI-driven user journeys

## 📝 **NEW: CommandLogger Integration (MANDATORY)**

### **Command Logging Requirements**
**ALL commands MUST use CommandLogger for structured logging and compliance tracking**:

```javascript
// Required in every command implementation - with shared session support
const createLogger = require('../../lib/logger.cjs');
const sessionId = process.env.ORCHESTRATOR_SESSION;
const logger = createLogger('command-name', sessionId);

// Log shared session usage (if orchestrator-driven)
if (sessionId) {
  logger.info('Using shared orchestrator session', { sessionId });
}

// Log command start
logger.start(task, options);

// Log delegation
logger.delegate('target-command', context, 'reason for delegation');

// Log violations
logger.violation('RULE_NAME', 'attempted action', 'severity');

// Log completion
logger.success(result);
// OR
logger.error('error message', details, isRecoverable);
```

### **Critical Infrastructure Rules**
```javascript
// ✅ REQUIRED: Check existing services
const apiCheck = await fetch('http://localhost:8084/health');
if (!apiCheck.ok) {
  logger.error('API not available - user must start it', { status: apiCheck.status }, false);
  return;
}

// ❌ FORBIDDEN: Server management
logger.violation('SERVER_MANAGED_BY_USER', 'attempted npm run dev', 'critical');
// await bash('npm run dev'); // NEVER DO THIS
```

### **Log File Structure**
```
.claude/logs/
├── orchestrator/2025-01-26.log    # Command-specific daily logs
├── data-setup/2025-01-26.log
├── app-discovery/2025-01-26.log
├── test-ui/2025-01-26.log
├── sessions/1737912345.log        # Full workflow sessions
├── compliance/2025-01-26.log      # Architectural violations
└── latest-session.log             # Current session (quick access)
```

### **Quick Log Access**
```bash
# Follow live execution (no more copy/paste!)
tail -f .claude/logs/latest-session.log

# Check violations
cat .claude/logs/compliance/$(date +%Y-%m-%d).log

# View specific command
cat .claude/logs/app-discovery/$(date +%Y-%m-%d).log

# Performance analysis
grep '"level":"END"' .claude/logs/*/$(date +%Y-%m-%d).log
```

### **Violation Tracking**
```javascript
// Common violations to track
logger.violation('SERVER_MANAGED_BY_USER', 'attempted server start', 'critical');
logger.violation('NO_DIRECT_COMMAND_CALLS', 'test-ui called data-setup directly', 'high');
logger.violation('SINGLE_RESPONSIBILITY', 'data-setup attempted UI interaction', 'medium');
logger.violation('COMMAND_TIMEOUT', 'exceeded 30s execution limit', 'medium');
```

### **Benefits of CommandLogger**
- **No more manual log copying**: All execution logged to files automatically
- **Violation alerts**: Immediate feedback on architectural breaches
- **Performance monitoring**: Automatic categorization (fast/normal/slow/very-slow)
- **Complete audit trail**: Full workflow visibility for debugging
- **Compliance tracking**: Dedicated violation logging for architecture review

### **Simple Data Operations**
```bash
# Direct delegation for pure data tasks
/data-setup "like from fiona to berry"
/data-setup "send messages in match berry/grace count=5"
```

### **Code Development Tasks**
```bash
# Route to appropriate development command
/architect "review profile architecture"
/refactor "improve authentication system"
```

## 🎯 Task Analysis Guidelines

### **Intent Detection Keywords**
- **UI Testing**: "test", "delete", "click", "hover", "message", "chat"
- **Data Preparation**: "create", "like", "match", "authenticate", "messages"
- **Architecture**: "review", "design", "refactor", "improve"
- **Discovery**: "discover", "find", "analyze", "map"

### **Complexity Assessment**
```javascript
// Simple task (direct delegation)
if (keywords.includes('like') && keywords.includes('from/to')) {
  return delegateTo('/data-setup', task)
}

// Complex task (orchestrated workflow)
if (keywords.includes('test') && keywords.includes('UI')) {
  return orchestratedWorkflow(['data-setup', 'app-discovery', 'test-ui'])
}
```

## 🔧 Error Handling Best Practices

### **Graceful Degradation**
```javascript
// Try primary approach
try {
  result = await primaryMethod()
} catch (error) {
  console.log(`⚠️ Primary method failed: ${error.message}`)

  // Fall back to alternative
  try {
    result = await fallbackMethod()
    console.log(`✅ Fallback successful`)
  } catch (fallbackError) {
    throw new Error(`Both methods failed: ${fallbackError.message}`)
  }
}
```

### **Clear Error Context**
```javascript
// ❌ UNHELPFUL
throw new Error("Failed")

// ✅ HELPFUL
throw new Error(`User '${userName}' not found. Available users: ${availableUsers.join(', ')}`)
```

### **Recovery Strategies**
```javascript
// Authentication failure → Try token refresh
// Data not found → Create minimal required data
// Chrome connection failed → Provide setup instructions
// API timeout → Retry with exponential backoff
```

## 📊 Output Standards

### **Human-Readable Summary**
```markdown
🎯 Task: [original request]
📋 Status: ✅ Success / ❌ Failed
⏱️ Duration: [actual time]
📊 Results: [specific outcomes]

🔍 Details:
- Step 1: [status] [details]
- Step 2: [status] [details]
- Final: [overall result]
```

### **Structured Data Output**
```json
{
  "success": true,
  "task": "original task description",
  "results": {
    "matchId": "uuid",
    "usersInvolved": ["TestMale", "TestFemale"],
    "messagesSent": 3
  },
  "uiTestingTokens": {
    "testmale": {
      "userId": "uuid",
      "token": "jwt-token",
      "name": "TestMale"
    }
  },
  "nextSteps": {
    "mainAppUrl": "http://localhost:3004",
    "suggestedTestUser": "testmale"
  }
}
```

## 🚀 Performance Optimization

### **Parallel Execution**
```bash
# ✅ CORRECT: Run independent operations in parallel
command1 &
command2 &
wait

# ❌ INEFFICIENT: Sequential when parallel is possible
command1
command2
```

### **Caching Strategy**
```javascript
// Cache user lookups, app discovery results
const userCache = new Map()
const discoveryCache = new Map()

async function getCachedUser(name) {
  if (userCache.has(name)) {
    return userCache.get(name)
  }
  const user = await fetchUser(name)
  userCache.set(name, user)
  return user
}
```

### **Resource Management**
```javascript
// Clean up test data after use
try {
  await runTest()
} finally {
  await cleanup()
}

// Close browser connections
await browserSession.close()
```

## 🧪 Testing Command Quality

### **Unit Test Checklist**
- [ ] Command handles invalid input gracefully
- [ ] All error cases return meaningful messages
- [ ] Success criteria are clearly met
- [ ] No side effects on other commands
- [ ] Cleanup happens even if command fails

### **Integration Test Scenarios**
- [ ] Command works standalone
- [ ] Command works when called by orchestrator
- [ ] Command works with real API data
- [ ] Command works with missing/invalid data
- [ ] Command respects architectural boundaries

### **Performance Benchmarks**
- [ ] Command completes within reasonable time
- [ ] Command doesn't consume excessive resources
- [ ] Command handles concurrent execution
- [ ] Command cleans up after itself

## 🔮 Future-Proofing Guidelines

### **Extensibility**
```javascript
// Design for easy feature addition
const handlers = {
  'create-user': handleUserCreation,
  'create-match': handleMatchCreation,
  // New handlers can be added here
}

function processTask(task) {
  for (const [pattern, handler] of Object.entries(handlers)) {
    if (task.includes(pattern)) {
      return handler(task)
    }
  }
  throw new Error(`Unknown task: ${task}`)
}
```

### **Configuration Management**
```javascript
// Centralized configuration
const CONFIG = {
  API_BASE: process.env.API_BASE || 'http://localhost:8084',
  JWT_SECRET: process.env.JWT_SECRET || 'dev-secret',
  TEST_USERS: {
    male: { name: 'TestMale', age: 28 },
    female: { name: 'TestFemale', age: 26 }
  }
}
```

### **Backward Compatibility**
```javascript
// Support old command syntax while introducing new
function parseTask(task) {
  // New syntax: "create match between TestMale and TestFemale"
  if (task.includes('between') && task.includes('and')) {
    return parseNewSyntax(task)
  }

  // Legacy syntax: "mutual-like TestMale TestFemale"
  return parseLegacySyntax(task)
}
```

## 🎯 Success Metrics

### **Command Quality Indicators**
- **Low error rate** (< 5% for common use cases)
- **Fast execution** (< 30 seconds for typical tasks)
- **Clear documentation** (examples, parameters, expected outcomes)
- **Architectural compliance** (no layer violations)
- **Reusability** (works in multiple contexts)

### **User Experience Metrics**
- **Time to complete task** (including setup)
- **Success rate** (first attempt works)
- **Error comprehension** (users understand what went wrong)
- **Learning curve** (easy to use correctly)

## 🎯 **2025 Architectural Updates Summary**

### **Major Changes Implemented**
1. **Option A Pure Validation**: data-setup only validates, test-ui handles all interactions
2. **CommandLogger Integration**: Mandatory logging for all commands with violation tracking
3. **SERVER_MANAGED_BY_USER**: Strict infrastructure management rules
4. **3-Step UI Workflow**: Validation → Discovery → Execution

### **Required Updates for Existing Commands**
```bash
# 1. Add CommandLogger to every command
const logger = createLogger('command-name');

# 2. Replace API data creation with UI flows
# OLD: API calls to create matches/messages
# NEW: UI interactions for complete user journeys

# 3. Add infrastructure compliance checks
const apiCheck = await fetch('http://localhost:8084/health');
if (!apiCheck.ok) {
  logger.error('Services not available', {}, false);
  return;
}

# 4. Log all violations immediately
logger.violation('RULE_NAME', 'violation details', 'severity');
```

### **Command Template Checklist**
- [ ] **Arguments**: Clear parameter specification
- [ ] **Success Criteria**: Specific, measurable outcomes
- [ ] **Description**: Single sentence describing purpose
- [ ] **CommandLogger integration**: All execution logged
- [ ] **Infrastructure compliance**: No server management
- [ ] **Pure SOC**: Single responsibility only
- [ ] **Error handling**: Graceful failure with logging

### **Benefits of New Architecture**
- **Elimination of JWT signature errors**: Real UI authentication
- **Complete workflow visibility**: No more copy/paste debugging
- **Architectural compliance enforcement**: Automatic violation detection
- **Better reliability**: UI-driven flows match real user behavior
- **Simplified command responsibilities**: Clear, single-purpose commands

This document serves as the **definitive guide** for building high-quality slash commands that follow TribeVibe's enhanced 2025 architectural principles while delivering excellent user experience with complete observability.