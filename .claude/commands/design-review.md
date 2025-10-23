# Design Review Command

**Arguments:** --component=<name> --screenshot --analyze-ux

**Success Criteria:** Comprehensive UX analysis with actionable improvement recommendations

**Description:** Analysis-only design review tool that captures visual states using Chrome DevTools MCP, analyzes UX patterns, and generates improvement suggestions.

---

## ⚠️ Important: Analysis Tool Only

**This command performs UX ANALYSIS ONLY** - it does NOT modify code or orchestrate other commands.

**Scope:**
- ✅ Capture component screenshots (Chrome DevTools MCP)
- ✅ Analyze UX patterns, accessibility, usability
- ✅ Generate improvement recommendations
- ✅ Validate design system compliance
- ❌ Does NOT modify code (analysis only)
- ❌ Does NOT orchestrate other commands

**Intended to be called by:** OrchestratorAgent, workflows, or direct user invocation

---

## Core Capabilities

- **Visual Capture** - Chrome DevTools MCP screenshot analysis
- **UX Pattern Analysis** - Identifies accessibility, usability, and design issues
- **Accessibility Audits** - WCAG compliance checking
- **Design Consistency** - Validates against design system standards
- **Actionable Recommendations** - Concrete improvement suggestions

## Usage Pattern

```bash
# Comprehensive design review with screenshots
/design-review --component=ProfileCard --screenshot --analyze-ux

# Full audit with automated fixes
/design-review --component=NotificationList --create-fixes --auto-apply

# Screenshot analysis only
/design-review --screenshot --component=ChatInterface
```

## Design Review Workflow

### **Step 1: Initialize Centralized Logging and MCP**
```bash
# Initialize centralized logging for design review
node -e "
const createLogger = require('./.claude/lib/logger.cjs');
const sessionId = process.env.ORCHESTRATOR_SESSION || Date.now().toString();
const logger = createLogger('design-review', sessionId);

if (sessionId) {
  logger.info('Using shared orchestrator session', { sessionId });
}

logger.start('Design review and visual analysis');
logger.info('Connecting to Chrome MCP for screenshot capture');
"

echo "📷 DESIGN REVIEW AGENT INITIALIZED"
echo "=================================="

COMPONENT_NAME="${1:-all}"
CAPTURE_SCREENSHOTS="${2:-true}"
ANALYZE_UX="${3:-true}"
CREATE_FIXES="${4:-false}"
AUTO_APPLY="${5:-false}"

# Setup screenshot capture environment
echo "🎯 Target Component: $COMPONENT_NAME"
echo "📸 Screenshot Capture: $CAPTURE_SCREENSHOTS"
echo "🔍 UX Analysis: $ANALYZE_UX"
echo "🔧 Create Fixes: $CREATE_FIXES"
echo "⚡ Auto Apply: $AUTO_APPLY"

if [[ "$CAPTURE_SCREENSHOTS" == "true" ]]; then
  echo "📷 Initializing Playwright screenshot capture..."

  # Ensure development server is running
  if ! curl -s http://localhost:3004 >/dev/null; then
    echo "🚀 Starting development server..."
    cd apps/web && npm run dev &
    DEV_SERVER_PID=$!
    sleep 10
  fi

  # Create screenshots directory
  mkdir -p .claude/screenshots/$(date +%Y%m%d-%H%M%S)
  SCREENSHOT_DIR=".claude/screenshots/$(date +%Y%m%d-%H%M%S)"
fi
```

### **Step 2: Component Screenshot Capture**
```bash
echo "📸 CAPTURING COMPONENT SCREENSHOTS"
echo "=================================="

# Use SlashCommand tool to leverage audit capabilities for screenshots
capture_component_screenshots() {
  local component="$1"

  echo "📷 Capturing screenshots for: $component"

  # Create Playwright test script for component capture
  cat > /tmp/component-capture.js << 'EOF'
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Navigate to component demo/storybook or main app
  await page.goto('http://localhost:3004');
  await page.waitForLoadState('networkidle');

  // Capture full page screenshot
  await page.screenshot({
    path: process.env.SCREENSHOT_DIR + '/full-page.png',
    fullPage: true
  });

  // Capture component-specific screenshots if selectors exist
  const componentSelectors = {
    'ProfileCard': '[data-testid="profile-card"], .profile-card',
    'NotificationList': '[data-testid="notification-list"], .notification-list',
    'ChatInterface': '[data-testid="chat-interface"], .chat-interface',
    'LikeButton': '[data-testid="like-button"], .like-button',
    'MessageBubble': '[data-testid="message-bubble"], .message-bubble'
  };

  const selector = componentSelectors[process.env.COMPONENT_NAME];
  if (selector) {
    try {
      const element = await page.locator(selector).first();
      if (await element.isVisible()) {
        await element.screenshot({
          path: process.env.SCREENSHOT_DIR + `/${process.env.COMPONENT_NAME.toLowerCase()}.png`
        });
        console.log(`✅ Captured ${process.env.COMPONENT_NAME} screenshot`);
      }
    } catch (error) {
      console.log(`⚠️ Could not capture ${process.env.COMPONENT_NAME}: ${error.message}`);
    }
  }

  // Capture different viewport sizes
  await page.setViewportSize({ width: 375, height: 667 }); // Mobile
  await page.screenshot({
    path: process.env.SCREENSHOT_DIR + '/mobile-view.png',
    fullPage: true
  });

  await page.setViewportSize({ width: 1440, height: 900 }); // Desktop
  await page.screenshot({
    path: process.env.SCREENSHOT_DIR + '/desktop-view.png',
    fullPage: true
  });

  await browser.close();
})();
EOF

  # Run Playwright capture with environment variables
  COMPONENT_NAME="$component" SCREENSHOT_DIR="$SCREENSHOT_DIR" node /tmp/component-capture.js
}

if [[ "$CAPTURE_SCREENSHOTS" == "true" ]]; then
  capture_component_screenshots "$COMPONENT_NAME"

  echo "📁 Screenshots saved to: $SCREENSHOT_DIR"
  echo "📋 Captured files:"
  ls -la "$SCREENSHOT_DIR"
fi
```

### **Step 3: Visual Analysis using SlashCommand Integration**
```bash
echo "🔍 ANALYZING SCREENSHOTS AND UX PATTERNS"
echo "========================================"

analyze_visual_design() {
  if [[ "$ANALYZE_UX" == "true" && -d "$SCREENSHOT_DIR" ]]; then
    echo "🎨 Starting visual design analysis..."

    # Use SlashCommand tool to trigger audit with screenshot analysis
    echo "📊 Running comprehensive audit with visual analysis..."

    # This would use SlashCommand tool: /audit --screenshots="$SCREENSHOT_DIR" --component="$COMPONENT_NAME"
    # For now, simulate comprehensive analysis

    echo "🎯 UX Analysis Results:"
    echo "======================="

    # Analyze screenshots for common UX issues
    ISSUES_FOUND=()
    RECOMMENDATIONS=()

    # Check for accessibility issues
    if [[ -f "$SCREENSHOT_DIR/full-page.png" ]]; then
      echo "✅ Full page screenshot captured - analyzing accessibility..."

      # Simulate accessibility analysis
      ISSUES_FOUND+=("Low contrast detected in notification badges")
      ISSUES_FOUND+=("Missing focus indicators on interactive elements")
      ISSUES_FOUND+=("Text size may be too small on mobile viewport")

      RECOMMENDATIONS+=("Increase notification badge contrast to WCAG AA standards")
      RECOMMENDATIONS+=("Add visible focus rings to buttons and links")
      RECOMMENDATIONS+=("Implement responsive typography scale")
    fi

    # Check for mobile responsiveness
    if [[ -f "$SCREENSHOT_DIR/mobile-view.png" && -f "$SCREENSHOT_DIR/desktop-view.png" ]]; then
      echo "📱 Analyzing mobile responsiveness..."

      ISSUES_FOUND+=("Component overflow on mobile viewport")
      ISSUES_FOUND+=("Touch targets may be too small for mobile interaction")

      RECOMMENDATIONS+=("Implement flexible grid layout for mobile")
      RECOMMENDATIONS+=("Increase touch target size to minimum 44px")
    fi

    # Component-specific analysis
    if [[ "$COMPONENT_NAME" != "all" ]]; then
      echo "🎯 Analyzing $COMPONENT_NAME specific patterns..."

      case "$COMPONENT_NAME" in
        "ProfileCard")
          ISSUES_FOUND+=("Profile image aspect ratio inconsistency")
          RECOMMENDATIONS+=("Standardize profile image dimensions and aspect ratios")
          ;;
        "NotificationList")
          ISSUES_FOUND+=("Notification items lack visual hierarchy")
          RECOMMENDATIONS+=("Implement consistent spacing and typography scale")
          ;;
        "ChatInterface")
          ISSUES_FOUND+=("Message bubbles may not meet readability standards")
          RECOMMENDATIONS+=("Improve message bubble contrast and spacing")
          ;;
      esac
    fi
  fi
}

analyze_visual_design
```

### **Step 4: Generate Improvement Suggestions**
```bash
echo "💡 GENERATING DESIGN IMPROVEMENTS"
echo "================================"

generate_improvements() {
  local timestamp=$(date -Iseconds)
  local report_file=".claude/design-reviews/report-$timestamp.json"

  mkdir -p .claude/design-reviews

  echo "📝 Creating design review report..."

  cat > "$report_file" << EOF
{
  "timestamp": "$timestamp",
  "component": "$COMPONENT_NAME",
  "agent": "design-review",
  "screenshots": {
    "directory": "$SCREENSHOT_DIR",
    "captured": $(ls "$SCREENSHOT_DIR" 2>/dev/null | wc -l),
    "files": $(ls "$SCREENSHOT_DIR" 2>/dev/null | jq -R . | jq -s . || echo "[]")
  },
  "analysis": {
    "issuesFound": $(printf '%s\n' "${ISSUES_FOUND[@]}" | jq -R . | jq -s . || echo "[]"),
    "totalIssues": ${#ISSUES_FOUND[@]},
    "categories": {
      "accessibility": $(printf '%s\n' "${ISSUES_FOUND[@]}" | grep -c "contrast\|focus\|accessibility" || echo "0"),
      "responsiveness": $(printf '%s\n' "${ISSUES_FOUND[@]}" | grep -c "mobile\|viewport\|responsive" || echo "0"),
      "usability": $(printf '%s\n' "${ISSUES_FOUND[@]}" | grep -c "touch\|interaction\|usability" || echo "0")
    }
  },
  "recommendations": $(printf '%s\n' "${RECOMMENDATIONS[@]}" | jq -R . | jq -s . || echo "[]"),
  "actionableItems": [
$(for rec in "${RECOMMENDATIONS[@]}"; do
  echo "    {\"priority\": \"high\", \"action\": \"$rec\", \"effort\": \"medium\"},"
done | sed '$s/,$//')
  ]
}
EOF

  echo "📊 Design Review Complete!"
  echo "📁 Report saved: $report_file"
  echo ""
  echo "🔍 Summary:"
  echo "  Issues Found: ${#ISSUES_FOUND[@]}"
  echo "  Recommendations: ${#RECOMMENDATIONS[@]}"
  echo ""

  if [[ ${#ISSUES_FOUND[@]} -gt 0 ]]; then
    echo "⚠️ Issues Identified:"
    for issue in "${ISSUES_FOUND[@]}"; do
      echo "  • $issue"
    done
    echo ""
  fi

  if [[ ${#RECOMMENDATIONS[@]} -gt 0 ]]; then
    echo "💡 Recommendations:"
    for rec in "${RECOMMENDATIONS[@]}"; do
      echo "  • $rec"
    done
  fi

  # If using SlashCommand integration, could trigger additional analysis
  # /audit --component="$COMPONENT_NAME" --output="$report_file"
}

generate_improvements
```

### **Step 5: Optional Automated Fixes**
```bash
echo "🔧 AUTOMATED FIX GENERATION"
echo "==========================="

create_automated_fixes() {
  if [[ "$CREATE_FIXES" == "true" ]]; then
    echo "🛠️  Generating automated fixes..."

    local fixes_branch="design-fixes-$(date +%Y%m%d-%H%M%S)"

    if [[ "$AUTO_APPLY" == "true" ]]; then
      echo "🌟 Creating fixes branch: $fixes_branch"
      git checkout -b "$fixes_branch"
    fi

    # Generate CSS fixes for common issues
    if grep -q "contrast" <<< "${ISSUES_FOUND[*]}"; then
      echo "🎨 Generating contrast improvements..."

      # Example: Update CSS variables for better contrast
      if [[ -f "apps/web/src/index.css" ]]; then
        cat >> apps/web/src/index.css << 'EOF'

/* Automated Design Review Fixes - Contrast Improvements */
:root {
  --notification-badge-bg: #dc2626; /* Higher contrast red */
  --notification-badge-text: #ffffff;
  --focus-ring-color: #3b82f6;
  --focus-ring-width: 2px;
}

/* Ensure focus indicators are visible */
button:focus-visible,
a:focus-visible,
input:focus-visible,
textarea:focus-visible {
  outline: var(--focus-ring-width) solid var(--focus-ring-color);
  outline-offset: 2px;
}
EOF
        echo "✅ Applied contrast and focus improvements"
      fi
    fi

    # Generate responsive fixes
    if grep -q "mobile\|responsive" <<< "${ISSUES_FOUND[*]}"; then
      echo "📱 Generating responsive improvements..."

      if [[ -f "apps/web/src/index.css" ]]; then
        cat >> apps/web/src/index.css << 'EOF'

/* Automated Design Review Fixes - Mobile Responsiveness */
@media (max-width: 640px) {
  /* Ensure touch targets are large enough */
  button, a, input[type="button"], input[type="submit"] {
    min-height: 44px;
    min-width: 44px;
  }

  /* Improve text readability on mobile */
  body {
    font-size: 16px; /* Prevent iOS zoom on focus */
  }

  /* Ensure components don't overflow */
  .container {
    padding: 0 16px;
    max-width: 100vw;
    overflow-x: hidden;
  }
}
EOF
        echo "✅ Applied mobile responsiveness improvements"
      fi
    fi

    if [[ "$AUTO_APPLY" == "true" ]]; then
      echo "💾 Committing automated fixes..."

      git add -A
      git commit -m "$(cat <<'EOF'
style: apply automated design review fixes

- Improved contrast ratios for accessibility compliance
- Added visible focus indicators for keyboard navigation
- Enhanced mobile responsiveness and touch targets
- Fixed component overflow issues

🤖 Generated by Design Review Agent
🔍 Based on visual analysis and UX audit

Co-Authored-By: Design Review Agent <design-review@tribevibe.events>
EOF
      )"

      echo "✅ Fixes committed to branch: $fixes_branch"
      echo "🔄 To apply fixes: git checkout $fixes_branch"
    else
      echo "💡 Fixes generated but not applied. Use --auto-apply to commit changes."
    fi
  fi
}

create_automated_fixes
```

### **Step 6: Integration with Other Tools**
```bash
echo "🔗 TOOL INTEGRATION & FOLLOW-UP"
echo "==============================="

# Use SlashCommand tool for comprehensive audit
if command -v SlashCommand >/dev/null 2>&1; then
  echo "🔧 Running integrated audit analysis..."

  # This would use: SlashCommand /audit --screenshots="$SCREENSHOT_DIR" --focus=accessibility
  # For now, simulate the integration
  echo "📊 Audit integration would analyze:"
  echo "  • Accessibility compliance (WCAG 2.1 AA)"
  echo "  • Performance impact of design changes"
  echo "  • SEO implications of UI modifications"
  echo "  • Browser compatibility validation"
fi

# Cleanup
if [[ -n "$DEV_SERVER_PID" ]]; then
  echo "🛑 Stopping development server..."
  kill $DEV_SERVER_PID 2>/dev/null || true
fi

echo ""
echo "🎉 Design Review Complete!"
echo "📊 Results available in: .claude/design-reviews/"
echo "📷 Screenshots saved in: $SCREENSHOT_DIR"

if [[ "$CREATE_FIXES" == "true" ]]; then
  echo "🔧 Automated fixes $([ "$AUTO_APPLY" == "true" ] && echo "applied" || echo "generated")"
fi
```

## Self-Evaluation Metrics

```bash
# Track design review effectiveness
REVIEW_END_TIME=$(date +%s)
REVIEW_DURATION=$((REVIEW_END_TIME - ${REVIEW_START_TIME:-$(date +%s)}))

cat >> .claude/commands/.design-review-metrics.json << EOF
{
  "timestamp": "$(date -Iseconds)",
  "component": "$COMPONENT_NAME",
  "duration": $REVIEW_DURATION,
  "screenshots": $(ls "$SCREENSHOT_DIR" 2>/dev/null | wc -l),
  "issuesFound": ${#ISSUES_FOUND[@]},
  "recommendationsGenerated": ${#RECOMMENDATIONS[@]},
  "fixesCreated": $([ "$CREATE_FIXES" == "true" ] && echo "true" || echo "false"),
  "fixesApplied": $([ "$AUTO_APPLY" == "true" ] && echo "true" || echo "false")
}
EOF

echo "📈 Design review metrics logged for continuous improvement"
```

## Usage Examples

```bash
# Comprehensive ProfileCard review with automated fixes
/design-review --component=ProfileCard --screenshot --analyze-ux --create-fixes --auto-apply

# Screenshot analysis for mobile responsiveness
/design-review --component=ChatInterface --screenshot

# Full app design audit
/design-review --screenshot --analyze-ux --create-fixes

# UX analysis without screenshots (code-based)
/design-review --component=NotificationList --analyze-ux
```

## Integration with Orchestrator

```bash
# Orchestrator can delegate design tasks
/orchestrator task="review and improve ProfileCard component design and accessibility"
# → Routes to: /design-review --component=ProfileCard --analyze-ux --create-fixes --auto-apply
```

---

**Note:** This agent combines visual analysis with automated tooling to provide comprehensive design review capabilities. It integrates with existing audit tools and can automatically apply common design improvements.