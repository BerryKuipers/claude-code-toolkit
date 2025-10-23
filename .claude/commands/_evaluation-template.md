# Command Evaluation Template

Add this section to the end of every command file to enable self-improvement:

## Command Evaluation and Self-Improvement

Each execution of this command is automatically evaluated and the command evolves based on learnings:

```bash
# Initialize evaluation metrics
EVAL_START_TIME=${START_TIME:-$(date +%s)}
EVAL_END_TIME=$(date +%s)
EXECUTION_TIME=$((EVAL_END_TIME - EVAL_START_TIME))
ISSUES_FOUND=0
SUCCESS_RATE=100

# Evaluation metrics specific to this command:
# - [Add command-specific metrics here]
# - Total execution time
# - Success/failure rates
# - Issues encountered and resolution time
# - User satisfaction indicators

# Track issues encountered
if [[ -f /tmp/command-issues.log ]]; then
  ISSUES_FOUND=$(wc -l < /tmp/command-issues.log)
  SUCCESS_RATE=$((100 - ISSUES_FOUND * 10))
fi

# Generate evaluation report (unless disabled)
if [[ "$*" != *"--no-eval"* ]]; then
  echo ""
  echo "📊 COMMAND EVALUATION REPORT"
  echo "============================"
  echo "⏱️  Execution time: ${EXECUTION_TIME}s"
  echo "🎯 Success rate: ${SUCCESS_RATE}%"
  echo "🚨 Issues found: ${ISSUES_FOUND}"

  # Performance classification
  PERFORMANCE_RATING=""
  if [[ $EXECUTION_TIME -lt 30 ]]; then
    PERFORMANCE_RATING="🟢 Excellent (<30s)"
  elif [[ $EXECUTION_TIME -lt 120 ]]; then
    PERFORMANCE_RATING="🟡 Good (<2min)"
  else
    PERFORMANCE_RATING="🔴 Needs optimization (>2min)"
  fi

  echo "📈 Performance: $PERFORMANCE_RATING"

  # CRITICAL: Use background task agents for sophisticated analysis and improvements
  COMMAND_NAME=$(basename "$0" .md)
  COMMAND_FILE=".claude/commands/${COMMAND_NAME}.md"

  if [[ -f "$COMMAND_FILE" ]]; then
    echo "🚀 LAUNCHING BACKGROUND IMPROVEMENT AGENTS..."

    # Agent 1: Performance Pattern Analysis
    echo "Agent 1: Analyzing execution patterns..."
    /command-analyzer --command=${COMMAND_NAME} --execution-time=${EXECUTION_TIME} --success-rate=${SUCCESS_RATE} --output=/tmp/${COMMAND_NAME}-analysis.json

    # Agent 2: Best Practice Recommendation Engine
    echo "Agent 2: Generating improvement recommendations..."
    /improvement-recommender --analysis-file=/tmp/${COMMAND_NAME}-analysis.json --command-file="$COMMAND_FILE" --output=/tmp/${COMMAND_NAME}-recommendations.json

    # Agent 3: Safe Auto-Update Agent
    echo "Agent 3: Applying safe improvements..."
    /command-updater --recommendations-file=/tmp/${COMMAND_NAME}-recommendations.json --command-file="$COMMAND_FILE" --create-backup

    # Agent 4: Regression Testing Agent
    echo "Agent 4: Validating command improvements..."
    /command-validator --updated-file="$COMMAND_FILE" --test-suite=${COMMAND_NAME} --output=/tmp/${COMMAND_NAME}-validation.json

    # Process agent results
    if [[ -f /tmp/${COMMAND_NAME}-recommendations.json ]]; then
      echo "📊 Background agents completed analysis:"
      RECOMMENDATIONS=$(cat /tmp/${COMMAND_NAME}-recommendations.json | jq '.recommendationsCount')
      APPLIED=$(cat /tmp/${COMMAND_NAME}-recommendations.json | jq '.appliedCount')
      echo "  🎯 Recommendations generated: $RECOMMENDATIONS"
      echo "  ✅ Improvements applied: $APPLIED"

      # Check if validation passed
      if [[ -f /tmp/${COMMAND_NAME}-validation.json ]]; then
        VALIDATION_PASSED=$(cat /tmp/${COMMAND_NAME}-validation.json | jq '.validationPassed')
        if [[ "$VALIDATION_PASSED" == "true" ]]; then
          echo "  ✅ Validation: All improvements verified safe"
        else
          echo "  ⚠️  Validation: Some improvements need manual review"
        fi
      fi
    else
      echo "⚠️  Background agents not available, falling back to basic improvements..."

      # Fallback to basic improvements
      # Create backup
      cp "$COMMAND_FILE" "${COMMAND_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

    # Store execution metrics for pattern analysis
    METRICS_FILE=".claude/commands/.${COMMAND_NAME}-metrics.json"
    cat >> "$METRICS_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "executionTime": ${EXECUTION_TIME},
  "successRate": ${SUCCESS_RATE},
  "issuesFound": ${ISSUES_FOUND},
  "performance": "$PERFORMANCE_RATING",
  "keyLearnings": [
    "$(if [[ $EXECUTION_TIME -gt 120 ]]; then echo "Optimize for faster execution"; fi)",
    "$(if [[ $ISSUES_FOUND -gt 0 ]]; then echo "Add more error handling"; fi)",
    "$(if [[ $SUCCESS_RATE -lt 90 ]]; then echo "Improve reliability patterns"; fi)"
  ]
}
EOF

    # Add lessons learned section if it doesn't exist
    if ! grep -q "## Lessons Learned" "$COMMAND_FILE"; then
      cat >> "$COMMAND_FILE" << 'LESSONS'

## Lessons Learned (Auto-Updated)

### Performance Optimizations:
- [Auto-populated based on execution metrics]

### Error Patterns Resolved:
- [Auto-populated based on issues encountered]

### Best Practices Discovered:
- [Auto-populated based on successful patterns]

### Next Iteration Goals:
- [Auto-populated based on improvement opportunities]
LESSONS
    fi

    echo "✅ Command file updated with execution insights"
    echo "💾 Metrics stored for continuous improvement"
  fi

  echo ""
  echo "🎯 COMMAND EVALUATION COMPLETE"
  echo "Evolution enabled: Command will improve with each use"
fi
```

## Usage Instructions

1. **Copy this template** to the end of any new command file
2. **Customize the metrics** section for command-specific measurements
3. **Ensure START_TIME** is set at the beginning of the command execution
4. **The evaluation runs automatically** unless `--no-eval` is passed

## Benefits

- **Self-improving commands** that get better with each use
- **Performance tracking** and optimization opportunities
- **Issue pattern recognition** and automated prevention
- **Command evolution** based on real usage data
- **Continuous learning** from every execution

This template ensures all TribeVibe commands continuously evolve and improve based on actual usage patterns and discovered issues.