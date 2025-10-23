# Command Performance Analyzer Agent

**Arguments:** --command=<name> --execution-time=<seconds> --success-rate=<percentage> --output=<file>

**Success Criteria:** Detailed performance analysis with actionable optimization recommendations

**Description:** Specialized background agent for analyzing command execution patterns, performance bottlenecks, and generating improvement recommendations. Designed for SlashCommand tool delegation.

## Agent Capabilities

- **Execution Pattern Analysis** - Identifies performance trends over time
- **Bottleneck Detection** - Pinpoints slow operations and resource constraints
- **Optimization Recommendations** - Suggests specific improvements based on data
- **Comparative Analysis** - Benchmarks against similar commands
- **Predictive Modeling** - Forecasts performance impact of changes

## Usage Pattern

```bash
# Invoked by parent commands via SlashCommand tool
/command-analyzer --command=db-manage --execution-time=120 --success-rate=95 --output=/tmp/db-manage-analysis.json
```

## Analysis Workflow

### **Step 1: Historical Data Collection**
```bash
echo "📊 Collecting historical performance data..."

COMMAND_NAME="$1"
EXECUTION_TIME="$2"
SUCCESS_RATE="$3"
OUTPUT_FILE="$4"
ANALYSIS_START_TIME=$(date +%s)

# Load historical metrics if available
METRICS_FILE=".claude/commands/.${COMMAND_NAME}-metrics.json"
HISTORICAL_DATA=()

if [[ -f "$METRICS_FILE" ]]; then
  # Read previous executions (last 10 entries)
  HISTORICAL_DATA=($(tail -10 "$METRICS_FILE" | jq -r '.executionTime // 0'))
  echo "📈 Found ${#HISTORICAL_DATA[@]} historical data points"
else
  echo "📋 No historical data available - this will establish baseline"
  touch "$METRICS_FILE"
fi
```

### **Step 2: Performance Trend Analysis**
```bash
echo "📈 Analyzing performance trends..."

# Calculate average execution time
if [[ ${#HISTORICAL_DATA[@]} -gt 0 ]]; then
  TOTAL_TIME=0
  for time in "${HISTORICAL_DATA[@]}"; do
    TOTAL_TIME=$((TOTAL_TIME + time))
  done
  AVERAGE_TIME=$((TOTAL_TIME / ${#HISTORICAL_DATA[@]}))

  # Determine performance trend
  PERFORMANCE_TREND="stable"
  if [[ $EXECUTION_TIME -gt $((AVERAGE_TIME + 30)) ]]; then
    PERFORMANCE_TREND="degrading"
  elif [[ $EXECUTION_TIME -lt $((AVERAGE_TIME - 30)) ]]; then
    PERFORMANCE_TREND="improving"
  fi

  echo "⏱️  Current: ${EXECUTION_TIME}s, Average: ${AVERAGE_TIME}s, Trend: $PERFORMANCE_TREND"
else
  AVERAGE_TIME=$EXECUTION_TIME
  PERFORMANCE_TREND="baseline"
  echo "📊 Establishing performance baseline: ${EXECUTION_TIME}s"
fi
```

### **Step 3: Bottleneck Detection**
```bash
echo "🔍 Detecting performance bottlenecks..."

BOTTLENECKS=()
OPTIMIZATION_OPPORTUNITIES=()

# Analyze execution time thresholds
if [[ $EXECUTION_TIME -gt 300 ]]; then
  BOTTLENECKS+=("Long execution time (>5 minutes) - Consider parallel operations")
  OPTIMIZATION_OPPORTUNITIES+=("parallel_processing")
fi

if [[ $EXECUTION_TIME -gt 120 ]]; then
  BOTTLENECKS+=("Moderate execution time (>2 minutes) - Review sequential operations")
  OPTIMIZATION_OPPORTUNITIES+=("operation_sequencing")
fi

# Analyze success rate patterns
if [[ $SUCCESS_RATE -lt 90 ]]; then
  BOTTLENECKS+=("Low success rate (<90%) - Improve error handling")
  OPTIMIZATION_OPPORTUNITIES+=("error_handling")
fi

if [[ $SUCCESS_RATE -lt 100 ]]; then
  BOTTLENECKS+=("Partial failures detected - Add validation steps")
  OPTIMIZATION_OPPORTUNITIES+=("input_validation")
fi

# Command-specific bottleneck analysis
case "$COMMAND_NAME" in
  "db-manage")
    if [[ $EXECUTION_TIME -gt 180 ]]; then
      BOTTLENECKS+=("Database operations may be slow - Consider connection pooling")
      OPTIMIZATION_OPPORTUNITIES+=("db_connection_optimization")
    fi
    ;;
  "pr-process")
    if [[ $EXECUTION_TIME -gt 240 ]]; then
      BOTTLENECKS+=("PR processing is slow - Consider automated checks")
      OPTIMIZATION_OPPORTUNITIES+=("automated_validation")
    fi
    ;;
  "refactor")
    if [[ $EXECUTION_TIME -gt 300 ]]; then
      BOTTLENECKS+=("Refactoring taking too long - Better change detection needed")
      OPTIMIZATION_OPPORTUNITIES+=("smart_change_detection")
    fi
    ;;
esac

echo "🚨 Identified ${#BOTTLENECKS[@]} bottlenecks"
echo "💡 Found ${#OPTIMIZATION_OPPORTUNITIES[@]} optimization opportunities"
```

### **Step 4: Optimization Recommendations**
```bash
echo "💡 Generating optimization recommendations..."

RECOMMENDATIONS=()

# Generate specific recommendations based on opportunities
for opportunity in "${OPTIMIZATION_OPPORTUNITIES[@]}"; do
  case "$opportunity" in
    "parallel_processing")
      RECOMMENDATIONS+=("Implement parallel database connectivity checks")
      RECOMMENDATIONS+=("Use background task agents for independent operations")
      ;;
    "operation_sequencing")
      RECOMMENDATIONS+=("Batch similar operations together")
      RECOMMENDATIONS+=("Cache frequently accessed data")
      ;;
    "error_handling")
      RECOMMENDATIONS+=("Add comprehensive input validation")
      RECOMMENDATIONS+=("Implement graceful error recovery")
      ;;
    "input_validation")
      RECOMMENDATIONS+=("Pre-validate all inputs before processing")
      RECOMMENDATIONS+=("Add safety checks for destructive operations")
      ;;
    "db_connection_optimization")
      RECOMMENDATIONS+=("Implement connection pooling")
      RECOMMENDATIONS+=("Use async database operations where possible")
      ;;
    "automated_validation")
      RECOMMENDATIONS+=("Add pre-commit hooks for validation")
      RECOMMENDATIONS+=("Implement automated testing before merge")
      ;;
    "smart_change_detection")
      RECOMMENDATIONS+=("Use AST analysis for precise change detection")
      RECOMMENDATIONS+=("Implement incremental change processing")
      ;;
  esac
done

# Add general best practices
RECOMMENDATIONS+=("Add progress indicators for long operations")
RECOMMENDATIONS+=("Implement command resumption capabilities")
RECOMMENDATIONS+=("Use background agents for complex analysis")

echo "📋 Generated ${#RECOMMENDATIONS[@]} optimization recommendations"
```

### **Step 5: Generate Analysis Report**
```bash
echo "📊 Generating performance analysis report..."

# Calculate performance score
PERFORMANCE_SCORE=100
if [[ $EXECUTION_TIME -gt 300 ]]; then PERFORMANCE_SCORE=$((PERFORMANCE_SCORE - 30)); fi
if [[ $EXECUTION_TIME -gt 120 ]]; then PERFORMANCE_SCORE=$((PERFORMANCE_SCORE - 20)); fi
if [[ $SUCCESS_RATE -lt 100 ]]; then PERFORMANCE_SCORE=$((PERFORMANCE_SCORE - (100 - SUCCESS_RATE))); fi

# Create structured analysis output
cat > "$OUTPUT_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "command": "$COMMAND_NAME",
  "analysis": {
    "executionTime": $EXECUTION_TIME,
    "averageTime": $AVERAGE_TIME,
    "performanceTrend": "$PERFORMANCE_TREND",
    "successRate": $SUCCESS_RATE,
    "performanceScore": $PERFORMANCE_SCORE,
    "historicalDataPoints": ${#HISTORICAL_DATA[@]}
  },
  "bottlenecks": [
$(IFS=$'\n'; for bottleneck in "${BOTTLENECKS[@]}"; do
  echo "    \"$bottleneck\""
done | sed '$!s/$/,/')
  ],
  "optimizationOpportunities": [
$(IFS=$'\n'; for opportunity in "${OPTIMIZATION_OPPORTUNITIES[@]}"; do
  echo "    \"$opportunity\""
done | sed '$!s/$/,/')
  ],
  "recommendations": [
$(IFS=$'\n'; for rec in "${RECOMMENDATIONS[@]}"; do
  echo "    \"$rec\""
done | sed '$!s/$/,/')
  ],
  "riskAssessment": {
    "performanceRisk": "$(if [[ $PERFORMANCE_SCORE -lt 70 ]]; then echo "HIGH"; elif [[ $PERFORMANCE_SCORE -lt 85 ]]; then echo "MEDIUM"; else echo "LOW"; fi)",
    "trendRisk": "$(if [[ "$PERFORMANCE_TREND" == "degrading" ]]; then echo "HIGH"; elif [[ "$PERFORMANCE_TREND" == "stable" ]]; then echo "LOW"; else echo "IMPROVING"; fi)",
    "reliabilityRisk": "$(if [[ $SUCCESS_RATE -lt 90 ]]; then echo "HIGH"; elif [[ $SUCCESS_RATE -lt 100 ]]; then echo "MEDIUM"; else echo "LOW"; fi)"
  },
  "nextActions": [
    "$(if [[ $PERFORMANCE_SCORE -lt 70 ]]; then echo "Immediate optimization required"; elif [[ $PERFORMANCE_SCORE -lt 85 ]]; then echo "Schedule performance improvements"; else echo "Monitor performance trends"; fi)",
    "$(if [[ ${#RECOMMENDATIONS[@]} -gt 5 ]]; then echo "Prioritize top 3 recommendations"; else echo "Implement all recommendations"; fi)",
    "$(if [[ ${#HISTORICAL_DATA[@]} -lt 5 ]]; then echo "Collect more performance data"; else echo "Analyze performance patterns"; fi)"
  ]
}
EOF

echo "✅ Performance analysis complete: $OUTPUT_FILE"
echo "📊 Performance Score: $PERFORMANCE_SCORE/100"
echo "📈 Trend: $PERFORMANCE_TREND"
echo "🎯 Recommendations: ${#RECOMMENDATIONS[@]}"
```

## Agent Self-Evaluation

```bash
# Track agent performance
AGENT_END_TIME=$(date +%s)
AGENT_EXECUTION_TIME=$((AGENT_END_TIME - ANALYSIS_START_TIME))

# Store agent metrics
cat >> .claude/commands/.command-analyzer-metrics.json << EOF
{
  "timestamp": "$(date -Iseconds)",
  "agentExecutionTime": $AGENT_EXECUTION_TIME,
  "analyzedCommand": "$COMMAND_NAME",
  "bottlenecksDetected": ${#BOTTLENECKS[@]},
  "recommendationsGenerated": ${#RECOMMENDATIONS[@]},
  "performanceScore": $PERFORMANCE_SCORE
}
EOF

echo "🤖 Agent analysis completed in ${AGENT_EXECUTION_TIME}s"
```

---

**Note:** This agent provides sophisticated performance analysis that would be too complex for inline implementation. It's designed to be invoked by other commands via SlashCommand tool for deep performance insights and optimization guidance.