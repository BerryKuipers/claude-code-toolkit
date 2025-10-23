# Conflict Resolution System

## 🤔 When Commands Disagree

Smart conflict resolution for when collaborating commands provide conflicting recommendations.

## 🎯 Conflict Resolution Rules

### Rule 1: Primary Command Authority
The command that initiated the collaboration has final authority:
```bash
# User runs: /refactor component
# Refactor suggests: "Extract 3 methods"
# Architect suggests: "Restructure entire class"
# Resolution: Refactor decides (initiated the task)
```

### Rule 2: Risk-Based Priority
Higher-risk recommendations override lower-risk ones:
```bash
# Database context
# DB-Manage suggests: "Optimize query indexes" (medium risk)
# Architect suggests: "Don't change schema during peak hours" (high risk)
# Resolution: Architect wins (higher risk awareness)
```

### Rule 3: User Confirmation for Complex Conflicts
When rules 1-2 can't resolve, prompt the user:
```bash
# Both commands have equal authority and risk
# Present options clearly
# Let user make the final decision
```

### Rule 4: Consensus Building
Multiple iterations to reach agreement:
```bash
# Commands negotiate through shared workspace
# Refined recommendations until convergence
# Orchestrator facilitates the conversation
```

## 🔧 Implementation in Orchestrator

```bash
### Conflict Resolution Engine (NEW)

RESOLVE_COMMAND_CONFLICT() {
  local PRIMARY_CMD="$1"
  local SECONDARY_CMD="$2"
  local PRIMARY_RECOMMENDATION="$3"
  local SECONDARY_RECOMMENDATION="$4"
  local CONFLICT_CONTEXT="$5"

  echo "🤔 COMMAND CONFLICT DETECTED"
  echo "=============================="
  echo "Primary: $PRIMARY_CMD recommends: $PRIMARY_RECOMMENDATION"
  echo "Secondary: $SECONDARY_CMD recommends: $SECONDARY_RECOMMENDATION"
  echo "Context: $CONFLICT_CONTEXT"

  # Rule 1: Primary Command Authority
  if [[ "$CONFLICT_TYPE" == "scope" || "$CONFLICT_TYPE" == "approach" ]]; then
    echo "📋 Applying Rule 1: Primary command authority"
    echo "✅ Resolution: $PRIMARY_CMD recommendation accepted"
    echo "💡 Rationale: Primary command initiated the task"
    RESOLUTION="$PRIMARY_RECOMMENDATION"
    return 0
  fi

  # Rule 2: Risk-Based Priority
  PRIMARY_RISK=$(get_risk_level "$PRIMARY_RECOMMENDATION")
  SECONDARY_RISK=$(get_risk_level "$SECONDARY_RECOMMENDATION")

  if [[ "$SECONDARY_RISK" > "$PRIMARY_RISK" ]]; then
    echo "🚨 Applying Rule 2: Risk-based priority"
    echo "✅ Resolution: $SECONDARY_CMD recommendation accepted"
    echo "💡 Rationale: Higher risk awareness ($SECONDARY_RISK > $PRIMARY_RISK)"
    RESOLUTION="$SECONDARY_RECOMMENDATION"
    return 0
  fi

  # Rule 3: User Confirmation
  if [[ "$CONFLICT_COMPLEXITY" == "high" ]]; then
    echo "👤 Applying Rule 3: User confirmation required"
    echo ""
    echo "🎯 CONFLICT RESOLUTION NEEDED"
    echo "=============================="
    echo "Option A (${PRIMARY_CMD}): $PRIMARY_RECOMMENDATION"
    echo "Option B (${SECONDARY_CMD}): $SECONDARY_RECOMMENDATION"
    echo ""
    echo "Which approach would you prefer?"
    echo "[A] ${PRIMARY_CMD}'s recommendation"
    echo "[B] ${SECONDARY_CMD}'s recommendation"
    echo "[C] Let commands negotiate further"
    echo ""
    read -p "Your choice [A/B/C]: " USER_CHOICE

    case "$USER_CHOICE" in
      "A"|"a") RESOLUTION="$PRIMARY_RECOMMENDATION" ;;
      "B"|"b") RESOLUTION="$SECONDARY_RECOMMENDATION" ;;
      "C"|"c") initiate_consensus_building "$PRIMARY_CMD" "$SECONDARY_CMD" ;;
      *) echo "Invalid choice. Defaulting to primary command."; RESOLUTION="$PRIMARY_RECOMMENDATION" ;;
    esac
    return 0
  fi

  # Rule 4: Consensus Building
  echo "🤝 Applying Rule 4: Consensus building"
  initiate_consensus_building "$PRIMARY_CMD" "$SECONDARY_CMD"
}

get_risk_level() {
  local RECOMMENDATION="$1"

  # Analyze recommendation for risk indicators
  if [[ "$RECOMMENDATION" =~ "delete"|"drop"|"remove" ]]; then
    echo "high"
  elif [[ "$RECOMMENDATION" =~ "modify"|"change"|"update" ]]; then
    echo "medium"
  else
    echo "low"
  fi
}

initiate_consensus_building() {
  local CMD1="$1"
  local CMD2="$2"

  echo "🤝 CONSENSUS BUILDING SESSION"
  echo "============================"
  echo "Commands will negotiate through shared workspace..."

  # Create negotiation workspace
  NEGOTIATION_WORKSPACE="$COLLABORATIVE_WORKSPACE/negotiation"
  mkdir -p "$NEGOTIATION_WORKSPACE"

  # Round 1: Each command explains their reasoning
  echo "Round 1: Detailed reasoning..."
  echo "$CMD1 - Please provide detailed reasoning for your recommendation:"
  # Command provides extended explanation

  echo "$CMD2 - Please provide detailed reasoning for your recommendation:"
  # Command provides extended explanation

  # Round 2: Each command addresses the other's concerns
  echo "Round 2: Address concerns..."
  echo "$CMD1 - How do you address $CMD2's concerns?"
  echo "$CMD2 - How do you address $CMD1's concerns?"

  # Round 3: Find middle ground
  echo "Round 3: Find compromise..."
  echo "Both commands: Can you find a middle-ground approach?"

  # If still no consensus, fall back to primary command authority
  echo "Final decision: Primary command authority (fallback)"
}
```

## 📋 Common Conflict Scenarios

### Scenario 1: Refactor vs Architect Scope Disagreement
```bash
Conflict: Refactor wants to "extract methods", Architect wants to "restructure class"
Context: Complex authentication component
Resolution: Rule 1 - Refactor authority (initiated task)
Outcome: Extract methods first, then consider restructuring later

Orchestrator Decision:
"✅ Refactor approach accepted: Extract methods for immediate improvement
💡 Architect concern noted: Schedule full restructure for next iteration
🔄 Compromise: Refactor creates extraction that enables future restructuring"
```

### Scenario 2: Database Risk Conflict
```bash
Conflict: DB-Manage wants "immediate index optimization", Architect warns "peak hours risk"
Context: Production database performance issue
Resolution: Rule 2 - Risk-based priority (Architect wins)
Outcome: Schedule optimization for off-peak hours

Orchestrator Decision:
"🚨 Architect safety concern takes priority: Peak hours risk too high
⏰ Rescheduled: Index optimization moved to 2 AM maintenance window
✅ Compromise: Implement temporary query optimization for immediate relief"
```

### Scenario 3: Complex Design Conflict
```bash
Conflict: Design-Review suggests "complete redesign", Refactor suggests "incremental improvement"
Context: User profile component with UX issues
Resolution: Rule 3 - User confirmation required
User Choice: Incremental improvement with design guidance

Orchestrator Decision:
"👤 User selected incremental approach with design constraints
🎨 Design-Review will provide incremental improvement guidelines
🔧 Refactor will implement changes following design principles
📋 Next iteration: Evaluate complete redesign based on user feedback"
```

### Scenario 4: Testing Strategy Conflict
```bash
Conflict: Test-All wants "full regression suite", Debug suggests "focused auth testing"
Context: Authentication bug fix
Resolution: Rule 4 - Consensus building
Outcome: Focused tests first, then targeted regression

Negotiated Resolution:
"🎯 Phase 1: Run focused authentication tests (Debug recommendation)
📊 Phase 2: If Phase 1 passes, run auth-related regression tests
⚡ Benefit: Faster feedback cycle while maintaining coverage
🤝 Both commands satisfied with phased approach"
```

## 🔄 Conflict Prevention

### Proactive Conflict Avoidance
```bash
# Orchestrator analyzes potential conflicts before starting collaboration
ANALYZE_POTENTIAL_CONFLICTS() {
  local TASK="$1"
  local COLLABORATORS=("${@:2}")

  echo "🔍 Analyzing potential conflicts for: $TASK"

  # Check for known conflict patterns
  if [[ " ${COLLABORATORS[*]} " =~ "refactor" ]] && [[ " ${COLLABORATORS[*]} " =~ "architect" ]]; then
    echo "⚠️  Potential scope conflict: refactor vs architect approaches"
    echo "💡 Mitigation: Set clear boundaries and sequence"
    CONFLICT_MITIGATION="scope_boundaries"
  fi

  if [[ " ${COLLABORATORS[*]} " =~ "db-manage" ]] && [[ "$ENVIRONMENT" == "production" ]]; then
    echo "⚠️  Potential risk conflict: database changes in production"
    echo "💡 Mitigation: Enhanced safety checks and timing constraints"
    CONFLICT_MITIGATION="risk_management"
  fi

  # Set up conflict prevention measures
  setup_conflict_prevention "$CONFLICT_MITIGATION"
}

setup_conflict_prevention() {
  local MITIGATION_TYPE="$1"

  case "$MITIGATION_TYPE" in
    "scope_boundaries")
      echo "🎯 Setting clear scope boundaries between collaborators"
      cat > "$COLLABORATIVE_WORKSPACE/boundaries.json" << EOF
{
  "refactor": {
    "scope": "code structure and method extraction",
    "authority": "immediate code changes",
    "defers_to_architect": "major structural decisions"
  },
  "architect": {
    "scope": "structural patterns and system design",
    "authority": "architectural constraints and guidance",
    "defers_to_refactor": "implementation details"
  }
}
EOF
      ;;
    "risk_management")
      echo "🛡️ Enhanced risk management protocols activated"
      SAFETY_CHECKS_ENABLED=true
      PRODUCTION_MODE=true
      ;;
  esac
}
```

## ✅ Resolution Quality Metrics

Track conflict resolution effectiveness:
```bash
TRACK_RESOLUTION_METRICS() {
  local RESOLUTION_METHOD="$1"
  local OUTCOME_QUALITY="$2"
  local TIME_TO_RESOLVE="$3"

  # Log to learning system
  cat >> ".claude/commands/.conflict-resolution-log.json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "method": "$RESOLUTION_METHOD",
  "quality": "$OUTCOME_QUALITY",
  "timeToResolve": "$TIME_TO_RESOLVE",
  "commandsInvolved": ["$PRIMARY_CMD", "$SECONDARY_CMD"],
  "effectiveness": "$(calculate_effectiveness "$OUTCOME_QUALITY" "$TIME_TO_RESOLVE")"
}
EOF
}
```

This conflict resolution system ensures that when commands disagree, there's always a clear, fair, and intelligent way to reach the best decision. The orchestrator becomes a skilled mediator that maintains collaboration while preventing deadlocks.

**Result: Commands can collaborate confidently knowing that any disagreements will be resolved intelligently and fairly.** 🤝