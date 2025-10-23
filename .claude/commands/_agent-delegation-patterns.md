# Agent Delegation Patterns for TribeVibe Commands

This guide outlines patterns for using the SlashCommand tool to orchestrate complex workflows through background task agents.

## Core Principles

1. **Single Responsibility Agents** - Each agent has one specialized purpose
2. **Structured Communication** - Agents communicate via JSON files in /tmp
3. **Graceful Fallbacks** - Parent commands handle agent unavailability
4. **Performance Tracking** - All agents self-evaluate and improve
5. **Composable Workflows** - Agents can be chained for complex operations

## Common Delegation Patterns

### **Pattern 1: Sequential Agent Chain**

Execute agents in sequence where each depends on the previous one's output:

```bash
# Parent command orchestrates sequential agents
echo "🚀 Launching sequential agent workflow..."

# Agent 1: Analysis
/data-analyzer --input=raw-data.json --output=/tmp/analysis-results.json

# Agent 2: Processing (depends on Agent 1)
if [[ -f /tmp/analysis-results.json ]]; then
  /data-processor --analysis-file=/tmp/analysis-results.json --output=/tmp/processed-data.json
fi

# Agent 3: Action (depends on Agent 2)
if [[ -f /tmp/processed-data.json ]]; then
  /action-executor --data-file=/tmp/processed-data.json --execute
fi
```

**Use Cases:**
- Database migration analysis → conflict detection → safe fixes
- Code analysis → refactoring recommendations → implementation
- Performance monitoring → bottleneck detection → optimization

### **Pattern 2: Parallel Agent Execution**

Launch multiple independent agents simultaneously:

```bash
# Parent command launches parallel agents
echo "🚀 Launching parallel agent analysis..."

# Start multiple agents in background
/performance-analyzer --target=database --output=/tmp/perf-analysis.json &
/security-scanner --target=codebase --output=/tmp/security-scan.json &
/dependency-checker --target=packages --output=/tmp/deps-check.json &

# Wait for all agents to complete
wait

# Process combined results
if [[ -f /tmp/perf-analysis.json && -f /tmp/security-scan.json && -f /tmp/deps-check.json ]]; then
  /report-aggregator --perf=/tmp/perf-analysis.json --security=/tmp/security-scan.json --deps=/tmp/deps-check.json --output=/tmp/combined-report.json
fi
```

**Use Cases:**
- Multi-aspect code analysis (performance, security, quality)
- Parallel database validation (dev, test, staging)
- Concurrent testing across multiple environments

### **Pattern 3: Conditional Agent Dispatch**

Launch different agents based on conditions or analysis results:

```bash
# Conditional agent dispatch based on analysis
ANALYSIS_RESULT=$(cat /tmp/initial-analysis.json | jq -r '.riskLevel')

case "$ANALYSIS_RESULT" in
  "HIGH")
    echo "🚨 High risk detected - launching comprehensive analysis agents..."
    /deep-security-scan --thorough --output=/tmp/security-deep.json
    /impact-analyzer --comprehensive --output=/tmp/impact-analysis.json
    /rollback-planner --create-plan --output=/tmp/rollback-plan.json
    ;;
  "MEDIUM")
    echo "⚠️  Medium risk - launching standard validation agents..."
    /standard-validator --input=/tmp/initial-analysis.json --output=/tmp/validation.json
    /change-reviewer --automated --output=/tmp/review.json
    ;;
  "LOW")
    echo "✅ Low risk - launching optimization agents..."
    /performance-optimizer --suggestions --output=/tmp/optimizations.json
    /best-practices-checker --recommendations --output=/tmp/best-practices.json
    ;;
esac
```

**Use Cases:**
- Risk-based testing strategies
- Dynamic resource allocation based on load
- Adaptive workflow execution based on context

### **Pattern 4: Agent Collaboration Network**

Agents communicate and coordinate with each other:

```bash
# Collaborative agent network
echo "🤝 Establishing agent collaboration network..."

# Central coordination agent
/workflow-coordinator --agents=analyzer,processor,executor --workspace=/tmp/shared

# Specialized agents register with coordinator
/data-analyzer --coordinator=/tmp/shared/coordinator.json --register
/data-processor --coordinator=/tmp/shared/coordinator.json --register
/action-executor --coordinator=/tmp/shared/coordinator.json --register

# Coordinator orchestrates the workflow
/workflow-coordinator --execute-workflow --workspace=/tmp/shared
```

**Use Cases:**
- Complex multi-step refactoring workflows
- Distributed testing across multiple systems
- Coordinated deployment pipelines

### **Pattern 5: Self-Improving Agent Loop**

Agents that analyze their own performance and improve their parent command:

```bash
# Self-improving agent loop
echo "🔄 Launching self-improvement workflow..."

# Performance analysis agent
/command-analyzer --command=${COMMAND_NAME} --execution-time=${EXECUTION_TIME} --output=/tmp/analysis.json

# Improvement recommendation agent
/improvement-recommender --analysis-file=/tmp/analysis.json --command-file=${COMMAND_FILE} --output=/tmp/recommendations.json

# Safe auto-update agent
/command-updater --recommendations-file=/tmp/recommendations.json --command-file=${COMMAND_FILE} --backup

# Validation agent
/command-validator --updated-file=${COMMAND_FILE} --test-baseline --output=/tmp/validation.json

# Learning agent stores patterns
/pattern-learner --execution-data=/tmp/analysis.json --improvements=/tmp/recommendations.json --validation=/tmp/validation.json
```

**Use Cases:**
- Continuous command improvement
- Automated optimization based on usage patterns
- Self-evolving workflow systems

## Agent Communication Protocols

### **Standard Agent Input/Output**

All agents follow consistent I/O patterns:

```json
// Standard Agent Input Format
{
  "requestId": "uuid",
  "timestamp": "2025-01-15T10:30:00Z",
  "parentCommand": "db-manage",
  "parameters": {
    "target": "database",
    "scope": "full-analysis"
  },
  "context": {
    "executionTime": 120,
    "previousResults": "/tmp/previous-analysis.json"
  }
}

// Standard Agent Output Format
{
  "requestId": "uuid",
  "agentName": "migrate-analysis",
  "timestamp": "2025-01-15T10:35:00Z",
  "executionTime": 45,
  "status": "completed|failed|partial",
  "results": {
    "summary": "Analysis completed successfully",
    "dataPoints": 150,
    "issuesFound": 3
  },
  "recommendations": [
    "Add conditional existence checks",
    "Implement transaction boundaries"
  ],
  "nextActions": [
    "Review safety issues",
    "Apply recommended fixes"
  ],
  "agentMetrics": {
    "performanceScore": 95,
    "accuracy": 98,
    "efficiency": 92
  }
}
```

### **Error Handling and Fallbacks**

```bash
# Robust error handling pattern
AGENT_TIMEOUT=300  # 5 minutes
AGENT_OUTPUT="/tmp/agent-result.json"

# Launch agent with timeout
timeout $AGENT_TIMEOUT /specialized-agent --input=data.json --output="$AGENT_OUTPUT" &
AGENT_PID=$!

# Wait for completion or timeout
if wait $AGENT_PID 2>/dev/null; then
  if [[ -f "$AGENT_OUTPUT" ]]; then
    AGENT_STATUS=$(cat "$AGENT_OUTPUT" | jq -r '.status // "unknown"')
    if [[ "$AGENT_STATUS" == "completed" ]]; then
      echo "✅ Agent completed successfully"
      # Process agent results
    else
      echo "⚠️  Agent completed with issues - falling back to basic operation"
      # Implement fallback logic
    fi
  else
    echo "❌ Agent failed to produce output - using fallback"
    # Implement fallback logic
  fi
else
  echo "⏰ Agent timeout - terminating and falling back"
  kill $AGENT_PID 2>/dev/null
  # Implement fallback logic
fi
```

## Best Practices for Agent Design

### **1. Agent Specialization**

```bash
# ✅ Good: Specialized agent with clear purpose
/migrate-conflict-detector --migrations-dir=src/db/migrations --output=conflicts.json

# ❌ Bad: Generic agent trying to do everything
/database-everything --analyze --migrate --test --optimize
```

### **2. Stateless Agent Design**

```bash
# ✅ Good: Stateless agent with explicit inputs
/performance-analyzer --baseline-file=baseline.json --current-metrics=metrics.json --output=analysis.json

# ❌ Bad: Stateful agent with hidden dependencies
/performance-analyzer --use-cached-data --remember-previous-run
```

### **3. Composable Agent Interfaces**

```bash
# ✅ Good: Composable agents that can be chained
/data-extractor --source=database --output=raw-data.json
/data-transformer --input=raw-data.json --rules=transform-rules.json --output=clean-data.json
/data-analyzer --input=clean-data.json --output=analysis.json

# ❌ Bad: Monolithic agent that can't be composed
/data-pipeline --extract-from-db --transform-with-rules --analyze-and-report
```

### **4. Comprehensive Error Reporting**

```bash
# Agent should report detailed error information
{
  "status": "failed",
  "error": {
    "code": "MIGRATION_CONFLICT",
    "message": "Column 'user_id' referenced before creation",
    "details": {
      "conflictingMigration": "003_add_user_column.sql",
      "referencingMigration": "002_create_user_table.sql",
      "suggestedFix": "Reorder migrations or add conditional logic"
    }
  },
  "partialResults": {
    "validMigrations": 15,
    "conflictingMigrations": 2
  }
}
```

## Testing Agent Workflows

### **Agent Integration Tests**

```bash
# Test agent integration in parent commands
test_agent_workflow() {
  echo "Testing agent workflow integration..."

  # Mock agent outputs for testing
  mkdir -p /tmp/test-agents
  echo '{"status":"completed","results":{"issuesFound":0}}' > /tmp/test-agents/mock-output.json

  # Override agent calls for testing
  export AGENT_TEST_MODE=true
  export MOCK_AGENT_OUTPUT="/tmp/test-agents/mock-output.json"

  # Run parent command
  /db-manage --validate --test-mode

  # Verify workflow completed correctly
  assert_file_exists "/tmp/migration-analysis.json"
  assert_json_field "/tmp/migration-analysis.json" ".status" "completed"
}
```

## Migration from Inline to Agent-Based

### **Before: Inline Complex Logic**

```bash
# Complex inline validation (hard to maintain)
echo "=== Complex Migration Validation ==="
cd services/api
# ... 200 lines of complex validation logic
# ... difficult to test, reuse, or optimize
```

### **After: Agent-Based Delegation**

```bash
# Simple agent delegation (maintainable)
echo "=== Migration Validation with Agents ==="
/migrate-analysis --project=tribevibe --migrations-dir=services/api/src/db/migrations --output=/tmp/analysis.json

if [[ -f /tmp/analysis.json ]]; then
  ISSUES=$(cat /tmp/analysis.json | jq '.criticalIssues')
  if [[ $ISSUES -gt 0 ]]; then
    /migrate-fix --analysis-file=/tmp/analysis.json --auto-fix
  fi
fi
```

This pattern transforms complex monolithic commands into orchestrated workflows of specialized, reusable, and testable agents.

---

**Note:** These patterns enable building sophisticated, maintainable, and scalable command workflows by leveraging the SlashCommand tool for agent coordination and delegation.