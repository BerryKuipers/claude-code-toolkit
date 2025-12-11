---
name: capture-pages
description: Automated screenshot capture of application pages for visual documentation with parallel agents and HTML reports
---

# Capture Pages - Automated Screenshot Documentation

**User-facing command for capturing screenshots of all application pages.**

## Important: Command Purpose

**This command is a USER INTERFACE** - it delegates all actual work to the **page-capture agent**.

**What this command does:**
- Parse user arguments (category, url, output path)
- Validate MCP chrome-devtools availability
- Delegate to page-capture agent with context

**What this command does NOT do:**
- Does NOT discover routes itself
- Does NOT capture screenshots itself
- Does NOT generate reports itself

**All actual work is done by:** `.claude/agents/page-capture.md`

## Usage

```bash
# Capture all pages (auto-discover routes)
/capture-pages

# Capture specific category
/capture-pages --category=building
/capture-pages --category=story
/capture-pages --category=settings

# Capture single page
/capture-pages --page=/characters

# Custom base URL
/capture-pages --url=http://localhost:3000

# Headed mode (visible browser)
/capture-pages --headed

# With custom output directory
/capture-pages --output=./screenshots/sprint-42
```

## Arguments

### Optional:
- `--category=<name>` - Category filter (building, story, blueprints, settings, playground, admin)
- `--page=<path>` - Single page to capture (e.g., /characters)
- `--url=<base-url>` - Base URL (defaults to http://localhost:5173 or from .env)
- `--output=<dir>` - Output directory (defaults to flow-captures/{timestamp})
- `--headed` - Run browser in headed mode (visible)
- `--slow` - Add delays between captures for debugging
- `--parallel` - Use parallel background agents for faster capture
- `--skip-auth` - Skip authentication step
- `--config=<path>` - Custom config file path

## Examples

### Example 1: Capture All Pages
```bash
/capture-pages
```

**What happens:**
1. Command parses arguments (no filters)
2. Delegates to page-capture agent
3. Agent discovers all routes from project
4. Captures screenshots of each page
5. Generates HTML report
6. Returns summary with locations

### Example 2: Capture Building Category
```bash
/capture-pages --category=building --parallel
```

**What happens:**
1. Command parses category=building
2. Delegates with parallel flag
3. Agent discovers building routes (/characters, /locations, etc.)
4. Launches background agents for parallel capture
5. Collects results from all agents
6. Generates combined report

### Example 3: Single Page Capture
```bash
/capture-pages --page=/characters --headed
```

**What happens:**
1. Command parses single page target
2. Agent opens visible browser (headed mode)
3. Navigates to /characters
4. Captures screenshot
5. Returns single-page result

### Example 4: Custom Configuration
```bash
/capture-pages --config=./capture-config.json --output=./review-screenshots
```

**What happens:**
1. Command loads custom config file
2. Uses config for route discovery and settings
3. Outputs to specified directory
4. Generates report at custom location

## Workflow

### Step 1: Environment Check

Verify prerequisites:
- Dev server running (check with curl/fetch)
- MCP chrome-devtools available (attempt tool call)
- Output directory writable

**If server not running:**
```markdown
Error: Cannot connect to http://localhost:5173

The development server doesn't appear to be running.

Please start it with:
  npm run dev
  # or
  pnpm dev

Then retry: /capture-pages
```

### Step 2: Parse Arguments

Extract and validate:
- Category filter (if any)
- Base URL
- Output directory
- Mode flags (headed, slow, parallel)
- Config overrides

### Step 3: Delegate to Page Capture Agent

Use natural language delegation:

```markdown
"I need to capture screenshots of application pages for visual documentation.

Capture Request:
- **Category**: ${CATEGORY || 'all'}
- **Base URL**: ${BASE_URL}
- **Single Page**: ${PAGE_PATH || 'none'}
- **Output Directory**: ${OUTPUT_DIR}
- **Mode**: ${headed ? 'headed' : 'headless'}
- **Parallel**: ${PARALLEL}

Requirements:
- Discover routes from project configuration
- Handle authentication if required
- Capture full-page screenshots
- Generate HTML report
- Use parallel agents if requested

Provide detailed capture summary with all screenshot locations."
```

### Step 4: Return Results

Present agent's report to user with:
- Total pages captured
- Categories covered
- Output directory location
- HTML report path
- Any errors or skipped pages
- Time taken

## Output Format

### Success Report

```markdown
# Page Capture Complete

**Status**: Success
**Duration**: 45 seconds
**Pages**: 24 captured, 2 skipped

## Output Location

flow-captures/2024-12-07-143052/

## Categories

### Building (7 pages)
- characters.png - /characters
- locations.png - /locations
- items.png - /items
- vehicles.png - /vehicles
- events.png - /events
- map.png - /map
- crew.png - /crew

### Story (6 pages)
- story-arcs.png - /story-arcs
- episodes.png - /episodes
- storylines.png - /storylines
- storyboard.png - /storyboard
- scenes.png - /scenes
- shots.png - /shots

### Settings (5 pages)
- universe-settings.png - /universe-settings
- user-settings.png - /user-settings
- theme-editor.png - /theme-editor
- universe-management.png - /universe-management
- help.png - /help

## Skipped

- /admin - Requires elevated permissions
- /debug - Development only route

## Report

Open: flow-captures/2024-12-07-143052/capture-report.html
```

### Error Report

```markdown
# Page Capture Failed

**Status**: Error
**Reason**: Development server not running

Cannot connect to http://localhost:5173

## Resolution

1. Start the development server:
   ```bash
   npm run dev
   ```

2. Retry the capture:
   ```bash
   /capture-pages
   ```

## Partial Results

If some pages were captured before failure, they are at:
flow-captures/2024-12-07-143052/partial/
```

## Available Categories

Based on common application patterns:

| Category | Description | Common Routes |
|----------|-------------|---------------|
| building | World-building pages | /characters, /locations, /items, /vehicles, /events |
| story | Story creation pages | /story-arcs, /episodes, /scenes, /shots |
| blueprints | Template pages | /blueprints, /*-blueprints |
| playground | Experimental/creator pages | /playground, /creator, /sketcher |
| production | Production/workflow pages | /production, /timeline |
| admin | Administrative pages | /admin, /data-manager |
| settings | Configuration pages | /*-settings, /help |
| hubs | Dashboard/hub pages | /world-building, /story-creation |

## Configuration File

Create `.capture-config.json` for project-specific settings:

```json
{
  "baseUrl": "http://localhost:5173",
  "outputDir": "flow-captures",
  "timeout": 30000,
  "categories": {
    "building": [
      "/characters",
      "/locations",
      "/items",
      "/vehicles",
      "/events",
      "/map",
      "/crew"
    ],
    "story": [
      "/story-arcs",
      "/episodes",
      "/storylines",
      "/storyboard",
      "/scenes",
      "/shots"
    ]
  },
  "auth": {
    "required": true,
    "loginUrl": "/login",
    "successSelector": ".user-avatar",
    "credentials": {
      "emailEnvVar": "TEST_USER_EMAIL",
      "passwordEnvVar": "TEST_USER_PASSWORD"
    }
  },
  "ignore": [
    "/admin",
    "/debug",
    "/**/internal/*"
  ],
  "waitFor": {
    "/characters": ".character-grid",
    "/map": ".map-container"
  }
}
```

## MCP Requirements

This command requires **MCP chrome-devtools** for full functionality.

**Setup:**
1. Install MCP chrome-devtools server
2. Start Chrome with remote debugging:
   ```bash
   chrome --remote-debugging-port=9222
   ```
3. Connect MCP server to Claude Code
4. Verify: `/capture-pages --page=/`

**If MCP unavailable:**
Command provides manual capture instructions with all routes listed.

## Integration

**Orchestrator Keywords:**
capture pages, screenshot all, visual documentation, page screenshots, capture screens, document UI

**Workflow Integration:**
```bash
# Before design review
/capture-pages --category=building --output=./review/before

# After implementing changes
/capture-pages --category=building --output=./review/after

# For PR documentation
/capture-pages --parallel --output=./pr-assets/screenshots

# Quick category capture
/capture-pages --category=story
```

## Benefits

- **Automated Discovery** - No manual route lists needed
- **Parallel Capture** - Fast multi-page capture with background agents
- **Visual Reports** - HTML gallery of all captured pages
- **Category Filtering** - Focus on specific areas
- **Flexible Configuration** - Project-specific settings via config file
- **MCP Integration** - Uses real browser for accurate captures
- **Graceful Fallback** - Works with manual mode if MCP unavailable

## See Also

- `.claude/agents/page-capture.md` - Agent that performs the actual capture
- `/test-ui` - UI testing with visual validation
- `/fix-e2e-tests` - E2E test fixing workflow
