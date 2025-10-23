# Collaborative Intelligence Patterns

## 🤝 Smart Command Collaboration Through Orchestrator Hub

The orchestrator can intelligently determine when commands should collaborate and coordinate their specialized expertise for optimal results.

## 🔄 Enhanced Collaboration Scenarios

### Scenario 1: Refactor + Architect Collaboration
```bash
# User runs: /refactor complex-component
# 1. Refactor analyzes scope and complexity
# 2. If complex architectural changes detected, consult orchestrator
# 3. Orchestrator brings in architect for structural guidance
# 4. Both work together with shared context

# In refactor command Step 8:
if [[ $COMPLEXITY_SCORE -gt 75 && $ARCHITECTURAL_CHANGES -gt 3 ]]; then
  COLLABORATIVE_TASK="architectural review and refactoring guidance for $TARGET_COMPONENT"
  echo "🏗️ Complex architectural changes detected - requesting architect collaboration"

  # Request collaborative workspace
  SlashCommand "/orchestrator" "task=\"$COLLABORATIVE_TASK\" mode=collaborative scope=\"$TARGET_COMPONENT\""
fi
```

### Scenario 2: Debug + Test-All Intelligence
```bash
# User runs: /debug
# 1. Debug identifies specific issue type
# 2. Based on issue, orchestrator determines best validation approach
# 3. Coordinates with test-all for focused testing

# In debug command Step 8:
case "$ROOT_CAUSE_TYPE" in
  "Authentication"|"Authorization")
    COLLABORATIVE_TASK="validate authentication fixes with focused auth testing for $AFFECTED_COMPONENT"
    SlashCommand "/orchestrator" "task=\"$COLLABORATIVE_TASK\" mode=collaborative focus=auth"
    ;;
  "Database"|"Performance")
    COLLABORATIVE_TASK="validate performance fixes with database-focused testing"
    SlashCommand "/orchestrator" "task=\"$COLLABORATIVE_TASK\" mode=collaborative focus=performance"
    ;;
esac
```

### Scenario 3: Issue-Pickup + Design-Review + Refactor Chain
```bash
# User runs: /issue-pickup-smart
# 1. Picks UI-related issue
# 2. Orchestrator chains: design-review → refactor → test-user-flow
# 3. Each command builds on previous results

# Enhanced orchestrator workflow:
if [[ "$ISSUE_TYPE" == "UI" && "$COMPLEXITY" == "high" ]]; then
  echo "🎨 Complex UI issue detected - orchestrating design-first workflow"

  # Sequential collaboration with shared workspace
  SlashCommand "/design-review" "component=$COMPONENT --workspace=$SHARED_WORKSPACE"
  # Wait for design recommendations
  SlashCommand "/refactor" "implement-design --input=$SHARED_WORKSPACE/design-recommendations.json"
  # Validate with user flows
  SlashCommand "/test-user-flow" "validate-ui-changes --workspace=$SHARED_WORKSPACE"
fi
```

## 🧠 Orchestrator Intelligence Enhancements

### Context-Aware Collaboration
```bash
# Enhanced orchestrator decision matrix
COLLABORATION_MATRIX() {
  case "$TASK_TYPE:$COMPLEXITY:$DOMAIN" in
    "refactoring:high:architecture")
      COLLABORATORS=("/refactor" "/architect")
      PATTERN="collaborative"
      WORKSPACE_SHARED=true
      ;;
    "debugging:medium:frontend")
      COLLABORATORS=("/debug" "/test-user-flow")
      PATTERN="sequential"
      CHROME_DEVTOOLS_REQUIRED=true
      ;;
    "performance:high:database")
      COLLABORATORS=("/debug" "/db-manage" "/test-all")
      PATTERN="sequential"
      VALIDATION_CRITICAL=true
      ;;
    "ui-redesign:medium:design")
      COLLABORATORS=("/design-review" "/refactor" "/test-user-flow")
      PATTERN="pipeline"
      USER_VALIDATION_REQUIRED=true
      ;;
  esac
}
```

### Shared Workspace Management
```bash
# Orchestrator creates collaborative workspace
COLLABORATIVE_WORKSPACE="/tmp/orchestrator-$SESSION_ID/collaborative"
mkdir -p "$COLLABORATIVE_WORKSPACE"

# Shared context file
cat > "$COLLABORATIVE_WORKSPACE/context.json" << EOF
{
  "task": "$ORIGINAL_TASK",
  "primaryCommand": "$PRIMARY_COMMAND",
  "collaborators": ["$COLLABORATOR1", "$COLLABORATOR2"],
  "sharedData": {
    "targetComponent": "$COMPONENT",
    "complexity": "$COMPLEXITY",
    "riskLevel": "$RISK_LEVEL"
  },
  "progress": {
    "completed": [],
    "inProgress": "$CURRENT_COMMAND",
    "pending": ["$NEXT_COMMAND"]
  }
}
EOF
```

## 🎯 Specific Refactor + Architect Collaboration

### Enhanced Refactor Command
```bash
# Add to refactor command after complexity analysis
### Step 7.5: Architectural Consultation (NEW)

if [[ $COMPLEXITY_SCORE -gt 70 || $ARCHITECTURAL_IMPACT == "high" ]]; then
  echo "🏗️ ARCHITECTURAL CONSULTATION REQUIRED"
  echo "====================================="

  # Determine what architect should focus on
  ARCHITECT_SCOPE=""
  if [[ $FILE_CHANGES -gt 5 ]]; then
    ARCHITECT_SCOPE="multi-file structural changes"
  elif [[ $PATTERN_CHANGES -gt 3 ]]; then
    ARCHITECT_SCOPE="design pattern modifications"
  elif [[ $DEPENDENCY_CHANGES -gt 2 ]]; then
    ARCHITECT_SCOPE="dependency architecture changes"
  fi

  echo "📋 Consultation scope: $ARCHITECT_SCOPE"
  echo "🎯 Target component: $TARGET_COMPONENT"

  # Request architectural guidance through orchestrator
  ARCHITECT_TASK="architectural review for refactoring: $ARCHITECT_SCOPE in $TARGET_COMPONENT"
  echo "🚀 Requesting: SlashCommand \"/orchestrator\" \"task=$ARCHITECT_TASK mode=collaborative\""

  # In real implementation, this would:
  # 1. Create shared workspace
  # 2. Architect analyzes structural implications
  # 3. Provides specific guidance for refactor scope
  # 4. Refactor proceeds with architectural constraints

  echo "⏳ Waiting for architectural guidance..."
  echo "📊 Expected guidance: structural patterns, dependency impacts, risk mitigation"
fi
```

### Enhanced Architect Command
```bash
# Architect command with collaboration awareness
### Collaborative Mode Support (NEW)

if [[ "$MODE" == "collaborative" && -n "$WORKSPACE" ]]; then
  echo "🤝 COLLABORATIVE MODE: Architect + Refactor"
  echo "=========================================="

  # Read shared context
  REFACTOR_CONTEXT=$(cat "$WORKSPACE/context.json" 2>/dev/null || echo "{}")
  TARGET_COMPONENT=$(echo "$REFACTOR_CONTEXT" | jq -r '.sharedData.targetComponent // "unknown"')
  COMPLEXITY=$(echo "$REFACTOR_CONTEXT" | jq -r '.sharedData.complexity // "medium"')

  echo "📋 Refactor context:"
  echo "  → Component: $TARGET_COMPONENT"
  echo "  → Complexity: $COMPLEXITY"

  # Focused architectural analysis for refactor scope only
  echo "🔍 Analyzing architectural implications for refactor scope..."

  # Generate refactor-specific architectural guidance
  cat > "$WORKSPACE/architect-guidance.json" << EOF
{
  "componentAnalysis": {
    "currentPatterns": ["$DETECTED_PATTERNS"],
    "structuralRisks": ["$IDENTIFIED_RISKS"],
    "recommendedApproach": "$REFACTOR_APPROACH"
  },
  "constraints": {
    "preserveInterfaces": $INTERFACE_PRESERVATION,
    "dependencyLimits": $MAX_DEPENDENCY_CHANGES,
    "testingRequirements": ["$TESTING_NEEDS"]
  },
  "guidance": {
    "safeRefactorSteps": ["$STEP1", "$STEP2", "$STEP3"],
    "warningAreas": ["$WARNING1", "$WARNING2"],
    "validationPoints": ["$VALIDATION1", "$VALIDATION2"]
  }
}
EOF

  echo "✅ Architectural guidance provided for refactor scope"
  echo "📁 Saved to: $WORKSPACE/architect-guidance.json"
fi
```

## 📊 Benefits of Collaborative Intelligence

### ✅ Enhanced Outcomes
- **Refactor + Architect:** Structural integrity maintained during complex refactoring
- **Debug + Test-All:** Issue-specific validation instead of full test suite
- **Design-Review + Refactor:** Implementation aligned with design principles
- **DB-Manage + Test-All:** Performance validation with database-specific tests

### ✅ Efficiency Gains
- **Scoped Collaboration:** Architect only reviews refactor scope, not entire system
- **Context Sharing:** No duplicate analysis between collaborating commands
- **Intelligent Routing:** Orchestrator knows when collaboration adds value
- **Resource Optimization:** Only brings in collaborators when beneficial

### ✅ Maintained Architecture
- **Hub Coordination:** All collaboration still goes through orchestrator
- **No Direct Calls:** Commands never call each other directly
- **Shared Workspace:** Clean handoff mechanisms between collaborators
- **Conflict Prevention:** Orchestrator manages resource access and timing

## 🔧 Implementation Pattern

```bash
# Standard pattern for any command requesting collaboration
COLLABORATION_REQUEST() {
  local TASK_DESCRIPTION="$1"
  local COLLABORATION_MODE="$2"
  local SPECIFIC_SCOPE="$3"

  echo "🤝 Requesting collaboration through orchestrator hub"
  echo "📋 Task: $TASK_DESCRIPTION"
  echo "🎯 Mode: $COLLABORATION_MODE"
  echo "📍 Scope: $SPECIFIC_SCOPE"

  # Always route through orchestrator
  SlashCommand "/orchestrator" "task=\"$TASK_DESCRIPTION\" mode=$COLLABORATION_MODE scope=\"$SPECIFIC_SCOPE\""
}
```

This collaborative intelligence pattern maintains the hub-and-spoke architecture while enabling smart command collaboration when it adds value. The orchestrator becomes even more intelligent by understanding when and how commands can work together effectively.

**Result: Commands remain self-contained but can intelligently collaborate through the orchestrator hub when complex tasks benefit from multiple areas of expertise.**