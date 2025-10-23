# Orchestrator Interface Standard

This document defines the standard interfaces that all commands should implement to work seamlessly with the orchestrator system.

## Standard Command Interface

All commands should support these standardized arguments and output formats to enable orchestrator integration:

### **Input Arguments**

```bash
# Standard orchestrator arguments
--orchestrator-session=<session-id>     # Session ID for coordination
--output-format=<json|text|mixed>        # Output format preference
--workspace=<path>                       # Shared workspace for collaboration
--input-file=<path>                      # Input data from previous command
--output-file=<path>                     # Where to write results
--collaborative                         # Enable collaborative mode
--support-mode                          # Running as support for another command
--task-context=<description>             # Original user task description
```

### **Standard Output Format**

All commands should produce a JSON summary when `--output-format=json`:

```json
{
  "orchestratorResult": {
    "commandName": "db-manage",
    "sessionId": "orch-1695556789",
    "status": "completed|partial|failed",
    "executionTime": 45,
    "startTime": "2025-09-24T15:30:00Z",
    "endTime": "2025-09-24T15:30:45Z"
  },
  "results": {
    "summary": "Database operations completed successfully",
    "operationsPerformed": ["migration-validation", "schema-sync", "performance-test"],
    "metricsCollected": {
      "migrationsApplied": 3,
      "issuesFound": 0,
      "performanceScore": 95
    },
    "outputFiles": [
      "/tmp/orchestrator-session/db-analysis.json",
      "/tmp/orchestrator-session/migration-report.txt"
    ]
  },
  "recommendations": [
    "Database performance is optimal",
    "Consider adding indexes for user queries"
  ],
  "nextActions": [
    "Ready for production deployment",
    "Monitor performance after deployment"
  ],
  "issues": [
    {
      "severity": "warning",
      "message": "Some deprecated columns detected",
      "resolution": "Schedule cleanup in next maintenance window"
    }
  ]
}
```

## Command Enhancement Patterns

### **Pattern 1: Basic Orchestrator Support**

Add to command workflow:

```bash
# Parse orchestrator arguments
ORCHESTRATOR_SESSION=""
OUTPUT_FORMAT="text"
WORKSPACE=""
INPUT_FILE=""
OUTPUT_FILE=""
COLLABORATIVE=false
SUPPORT_MODE=false
TASK_CONTEXT=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --orchestrator-session=*)
      ORCHESTRATOR_SESSION="${1#*=}"
      shift ;;
    --output-format=*)
      OUTPUT_FORMAT="${1#*=}"
      shift ;;
    --workspace=*)
      WORKSPACE="${1#*=}"
      shift ;;
    --input-file=*)
      INPUT_FILE="${1#*=}"
      shift ;;
    --output-file=*)
      OUTPUT_FILE="${1#*=}"
      shift ;;
    --collaborative)
      COLLABORATIVE=true
      shift ;;
    --support-mode)
      SUPPORT_MODE=true
      shift ;;
    --task-context=*)
      TASK_CONTEXT="${1#*=}"
      shift ;;
    *)
      # Handle command-specific arguments
      shift ;;
  esac
done

# Set defaults if orchestrator session is provided
if [[ -n "$ORCHESTRATOR_SESSION" ]]; then
  WORKSPACE=${WORKSPACE:-"/tmp/orchestrator-$ORCHESTRATOR_SESSION"}
  OUTPUT_FILE=${OUTPUT_FILE:-"$WORKSPACE/${COMMAND_NAME}-result.json"}
  OUTPUT_FORMAT=${OUTPUT_FORMAT:-"json"}
fi
```

### **Pattern 2: Collaborative Mode Support**

```bash
if [[ "$COLLABORATIVE" == true && -n "$WORKSPACE" ]]; then
  echo "🤝 Enabling collaborative mode..."

  # Register with coordination system
  cat > "$WORKSPACE/${COMMAND_NAME}-registration.json" << EOF
{
  "commandName": "$COMMAND_NAME",
  "pid": $$,
  "startTime": "$(date -Iseconds)",
  "status": "running",
  "capabilities": ["analysis", "validation", "reporting"]
}
EOF

  # Check for shared data from other commands
  if [[ -f "$WORKSPACE/shared-context.json" ]]; then
    SHARED_CONTEXT=$(cat "$WORKSPACE/shared-context.json")
    echo "📊 Using shared context from other agents"
  fi
fi
```

### **Pattern 3: Result Standardization**

```bash
# At end of command execution
generate_orchestrator_result() {
  local command_name="$1"
  local status="$2"
  local summary="$3"

  if [[ "$OUTPUT_FORMAT" == "json" && -n "$OUTPUT_FILE" ]]; then
    cat > "$OUTPUT_FILE" << EOF
{
  "orchestratorResult": {
    "commandName": "$command_name",
    "sessionId": "$ORCHESTRATOR_SESSION",
    "status": "$status",
    "executionTime": $(($(date +%s) - $START_TIME)),
    "startTime": "$(date -d @$START_TIME -Iseconds)",
    "endTime": "$(date -Iseconds)"
  },
  "results": {
    "summary": "$summary",
    "operationsPerformed": $(printf '%s\n' "${OPERATIONS[@]}" | jq -R . | jq -s .),
    "metricsCollected": $METRICS_JSON,
    "outputFiles": $(printf '%s\n' "${OUTPUT_FILES[@]}" | jq -R . | jq -s .)
  },
  "recommendations": $(printf '%s\n' "${RECOMMENDATIONS[@]}" | jq -R . | jq -s .),
  "nextActions": $(printf '%s\n' "${NEXT_ACTIONS[@]}" | jq -R . | jq -s .),
  "issues": $(printf '%s\n' "${ISSUES[@]}" | jq -R . | jq -s .)
}
EOF
  fi
}

# Usage
generate_orchestrator_result "$COMMAND_NAME" "completed" "Command executed successfully"
```

## Enhanced Command Examples

### **db-manage with Orchestrator Support**

```bash
# Enhanced db-manage command with orchestrator integration
echo "🎯 DB-MANAGE WITH ORCHESTRATOR INTEGRATION"

# Parse orchestrator arguments (use pattern above)

# If collaborative mode, share database status
if [[ "$COLLABORATIVE" == true ]]; then
  # Share database connectivity status
  cat > "$WORKSPACE/database-status.json" << EOF
{
  "devDatabase": {
    "status": "connected",
    "port": 5434,
    "migrationsApplied": 13
  },
  "testDatabase": {
    "status": "connected",
    "port": 5435,
    "migrationsApplied": 13
  }
}
EOF
fi

# Use shared context if available
if [[ -f "$WORKSPACE/previous-analysis.json" ]]; then
  PREVIOUS_ISSUES=$(cat "$WORKSPACE/previous-analysis.json" | jq '.criticalIssues // 0')
  if [[ $PREVIOUS_ISSUES -gt 0 ]]; then
    echo "🚨 Previous analysis found $PREVIOUS_ISSUES issues - prioritizing fixes"
  fi
fi

# Execute command logic...

# Generate standardized result
OPERATIONS=("migration-validation" "schema-sync" "performance-test")
RECOMMENDATIONS=("Database performance optimal" "Consider adding user query indexes")
NEXT_ACTIONS=("Ready for production deployment")
ISSUES=()

generate_orchestrator_result "db-manage" "completed" "Database operations completed successfully"
```

### **test-user-flow with Orchestrator Support**

```bash
# Enhanced test-user-flow with orchestrator integration
echo "🧪 TEST-USER-FLOW WITH ORCHESTRATOR INTEGRATION"

# Use shared database status if available
if [[ -f "$WORKSPACE/database-status.json" ]]; then
  DB_STATUS=$(cat "$WORKSPACE/database-status.json" | jq -r '.testDatabase.status')
  if [[ "$DB_STATUS" != "connected" ]]; then
    echo "⚠️ Test database not ready - deferring until database is available"
    exit 0
  fi
fi

# Execute test workflow...

# Share test results for other commands
if [[ "$COLLABORATIVE" == true ]]; then
  cat > "$WORKSPACE/test-results.json" << EOF
{
  "testsPassed": $TESTS_PASSED,
  "testsFailed": $TESTS_FAILED,
  "criticalFlows": ["login", "registration", "profile-update"],
  "performanceMetrics": {
    "averageResponseTime": "${AVERAGE_RESPONSE_TIME}ms",
    "slowestEndpoint": "$SLOWEST_ENDPOINT"
  }
}
EOF
fi

# Generate result
OPERATIONS=("user-flow-validation" "api-endpoint-testing" "performance-measurement")
generate_orchestrator_result "test-user-flow" "completed" "User flow testing completed"
```

## Command Registration

Commands should self-register their capabilities:

```bash
# Create capability registration
register_command_capabilities() {
  local command_name="$1"

  mkdir -p .claude/orchestrator/capabilities
  cat > ".claude/orchestrator/capabilities/${command_name}.json" << EOF
{
  "commandName": "$command_name",
  "categories": ["database", "testing", "analysis"],
  "capabilities": ["migration-validation", "schema-analysis", "performance-testing"],
  "inputFormats": ["json", "text"],
  "outputFormats": ["json", "text", "mixed"],
  "collaborationSupported": true,
  "supportModeCapable": true,
  "estimatedDuration": "2-5min",
  "riskLevel": "low",
  "dependencies": ["database", "config"],
  "tags": ["database", "migration", "validation"]
}
EOF
}

# Register capabilities on command installation
register_command_capabilities "db-manage"
```

## Testing Orchestrator Integration

Commands should include orchestrator integration tests:

```bash
test_orchestrator_integration() {
  echo "🧪 Testing orchestrator integration..."

  # Test 1: JSON output format
  TEST_SESSION="test-$(date +%s)"
  TEST_WORKSPACE="/tmp/orchestrator-$TEST_SESSION"
  mkdir -p "$TEST_WORKSPACE"

  $COMMAND_NAME --orchestrator-session="$TEST_SESSION" --output-format=json --workspace="$TEST_WORKSPACE" test-args

  # Verify JSON output
  if [[ -f "$TEST_WORKSPACE/${COMMAND_NAME}-result.json" ]]; then
    if jq empty "$TEST_WORKSPACE/${COMMAND_NAME}-result.json" 2>/dev/null; then
      echo "✅ JSON output format test passed"
    else
      echo "❌ Invalid JSON output"
    fi
  else
    echo "❌ No JSON output file created"
  fi

  # Test 2: Collaborative mode
  echo '{"testData": "shared"}' > "$TEST_WORKSPACE/shared-context.json"
  $COMMAND_NAME --collaborative --workspace="$TEST_WORKSPACE" test-args

  if [[ -f "$TEST_WORKSPACE/${COMMAND_NAME}-registration.json" ]]; then
    echo "✅ Collaborative mode test passed"
  else
    echo "❌ Collaborative registration failed"
  fi

  # Cleanup
  rm -rf "$TEST_WORKSPACE"
}
```

---

**Implementation Priority:**
1. **High Priority**: db-manage, test-user-flow, pr-process
2. **Medium Priority**: refactor, debug, command-analyzer
3. **Low Priority**: Utility and helper commands

This standard enables seamless orchestrator integration while maintaining backward compatibility for standalone command usage.