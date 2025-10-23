# System Discovery - TribeVibe Functionality Overview

**Arguments**: `[--type=pages|features|api|all] [--output=json|text]` (optional filters)
**Success Criteria**: Gather comprehensive overview of TribeVibe system functionality
**Description**: Provides system functionality overview for UI testing planning and feature discovery

## Purpose
- **System Overview**: Catalog all known pages, features, and API endpoints
- **Testing Planning**: Provide structured data for UI test scenario planning
- **Feature Discovery**: Document available functionality for new developers/testers
- **API Mapping**: List known API contracts and endpoints

## Command Execution

This command is designed to be called by the orchestrator or UI frontend agent to gather system information.

## Implementation

```javascript
const createLogger = require('../lib/logger.cjs');
const sessionId = process.env.ORCHESTRATOR_SESSION || `system-discovery-${Date.now()}`;
const logger = createLogger('system-discovery', sessionId);

async function executeSystemDiscovery(args = {}) {
  logger.start('System Discovery');

  try {
    const { type = 'all', output = 'json' } = args;

    // Gather system information
    const systemInfo = await gatherSystemInformation(type);

    // Format output
    const result = {
      ok: true,
      type: type,
      timestamp: new Date().toISOString(),
      systemInfo: systemInfo
    };

    if (output === 'json') {
      logger.success(result);
      return result;
    } else {
      return formatTextOutput(systemInfo);
    }

  } catch (error) {
    logger.error(`System discovery failed: ${error.message}`);
    return {
      ok: false,
      error: error.message,
      timestamp: new Date().toISOString()
    };
  }
}

async function gatherSystemInformation(type) {
  const systemInfo = {};

  if (type === 'all' || type === 'pages') {
    systemInfo.pages = await discoverPages();
  }

  if (type === 'all' || type === 'features') {
    systemInfo.features = await discoverFeatures();
  }

  if (type === 'all' || type === 'api') {
    systemInfo.apiEndpoints = await discoverApiEndpoints();
  }

  return systemInfo;
}

async function discoverPages() {
  return [
    {
      name: "login",
      route: "/auth/login",
      description: "User authentication page",
      type: "auth",
      selectors: {
        form: "form#login, .login-form",
        emailInput: "input[name='email'], input[type='email']",
        passwordInput: "input[name='password'], input[type='password']",
        submitButton: "button[type='submit'], .btn-login"
      }
    },
    {
      name: "register",
      route: "/auth/register",
      description: "User registration page",
      type: "auth",
      selectors: {
        form: "form#register, .register-form",
        nameInput: "input[name='name'], input[placeholder*='name' i]",
        emailInput: "input[name='email'], input[type='email']",
        passwordInput: "input[name='password'], input[type='password']",
        submitButton: "button[type='submit'], .btn-register"
      }
    },
    {
      name: "profile",
      route: "/profile",
      description: "Current user profile management",
      type: "profile",
      selectors: {
        editButton: ".btn-edit, [data-action='edit']",
        bioField: "textarea[name='bio'], .bio-input",
        interestsField: "input[name='interests'], .interests-input",
        saveButton: ".btn-save, [data-action='save']"
      }
    },
    {
      name: "profile-detail",
      route: "/profile/:id",
      description: "View other user profiles",
      type: "profile",
      selectors: {
        likeButton: ".btn-like, [data-action='like']",
        passButton: ".btn-pass, [data-action='pass']",
        profileImage: ".profile-image, .user-avatar",
        profileInfo: ".profile-info, .user-details"
      }
    },
    {
      name: "discover",
      route: "/browse",
      description: "Browse potential matches",
      type: "matching",
      selectors: {
        profileCards: ".profile-card, .user-card",
        likeButton: ".btn-like, [data-action='like']",
        passButton: ".btn-pass, [data-action='pass']",
        nextProfile: ".btn-next, [data-action='next']"
      }
    },
    {
      name: "matches",
      route: "/matches",
      description: "View mutual matches",
      type: "matching",
      selectors: {
        matchList: ".match-list, .matches-container",
        matchCard: ".match-card, .match-item",
        chatButton: ".btn-chat, [data-action='chat']",
        matchDate: ".match-date, .matched-on"
      }
    },
    {
      name: "chat",
      route: "/matches/:matchId/chat",
      description: "Chat with matches",
      type: "messaging",
      selectors: {
        messagesList: ".messages-list, .chat-messages",
        messageInput: ".message-input, input[name='message']",
        sendButton: ".btn-send, [data-action='send']",
        messageItem: ".message-item, .chat-message",
        reactionButton: ".btn-reaction, [data-action='react']",
        emoticonButton: ".btn-emoticon, [data-action='emoticon']"
      }
    },
    {
      name: "simulation",
      route: "/simulation",
      description: "Development simulation dashboard",
      type: "dev",
      selectors: {
        userGrid: ".user-grid, .simulation-users",
        createUserButton: ".btn-create-user, [data-action='create']",
        statsPanel: ".stats-panel, .simulation-stats"
      }
    },
    {
      name: "admin",
      route: "/admin",
      description: "Administrative interface",
      type: "admin",
      selectors: {
        userManagement: ".user-management, .admin-users",
        systemStats: ".system-stats, .admin-dashboard",
        actionButtons: ".admin-action, [data-admin-action]"
      }
    }
  ];
}

async function discoverFeatures() {
  return [
    {
      name: "like",
      description: "Like other users to create potential matches",
      category: "matching",
      actions: [
        { action: "click like button", selector: ".btn-like, [data-action='like']" },
        { action: "create potential match", result: "match notification or immediate match" }
      ],
      relatedPages: ["discover", "profile-detail"]
    },
    {
      name: "pass",
      description: "Pass on users to remove from discovery",
      category: "matching",
      actions: [
        { action: "click pass button", selector: ".btn-pass, [data-action='pass']" },
        { action: "remove from discover", result: "user no longer shown in browse" }
      ],
      relatedPages: ["discover", "profile-detail"]
    },
    {
      name: "chat",
      description: "Send and receive messages with matches",
      category: "messaging",
      actions: [
        { action: "send message", selector: ".message-input, .btn-send" },
        { action: "view conversation history", selector: ".messages-list" },
        { action: "scroll through messages", result: "load message history" }
      ],
      relatedPages: ["chat", "matches"]
    },
    {
      name: "reactions",
      description: "React to messages with emojis",
      category: "messaging",
      actions: [
        { action: "add emoji reaction", selector: ".btn-reaction, [data-action='react']" },
        { action: "remove reaction", selector: ".reaction-item[data-action='remove']" },
        { action: "view reactions", result: "see who reacted to message" }
      ],
      relatedPages: ["chat"]
    },
    {
      name: "emoticons",
      description: "Send emoticons in messages",
      category: "messaging",
      actions: [
        { action: "select emoticon", selector: ".btn-emoticon, [data-action='emoticon']" },
        { action: "send in message", result: "emoticon appears in chat" }
      ],
      relatedPages: ["chat"]
    },
    {
      name: "notifications",
      description: "System notifications for matches and messages",
      category: "notifications",
      actions: [
        { action: "view notifications", selector: ".notifications, .notification-list" },
        { action: "mark as read", selector: "[data-action='mark-read']" },
        { action: "notification click", result: "navigate to relevant page" }
      ],
      relatedPages: ["matches", "chat"]
    },
    {
      name: "profile-edit",
      description: "Edit profile information and preferences",
      category: "profile",
      actions: [
        { action: "update bio", selector: "textarea[name='bio'], .bio-input" },
        { action: "change photos", selector: ".photo-upload, [data-action='upload']" },
        { action: "edit interests", selector: ".interests-input, [name='interests']" },
        { action: "save changes", selector: ".btn-save, [data-action='save']" }
      ],
      relatedPages: ["profile"]
    },
    {
      name: "admin-actions",
      description: "Administrative functions for system management",
      category: "admin",
      actions: [
        { action: "user management", selector: ".user-management, .admin-users" },
        { action: "system monitoring", selector: ".system-stats, .admin-dashboard" },
        { action: "data operations", selector: "[data-admin-action]" }
      ],
      relatedPages: ["admin"]
    }
  ];
}

async function discoverApiEndpoints() {
  return [
    {
      endpoint: "/api/auth/login",
      method: "POST",
      description: "User authentication",
      category: "auth",
      payload: { email: "string", password: "string" },
      response: { token: "jwt", user: "UserProfile" }
    },
    {
      endpoint: "/api/auth/register",
      method: "POST",
      description: "User registration",
      category: "auth",
      payload: { name: "string", email: "string", password: "string" },
      response: { token: "jwt", user: "UserProfile" }
    },
    {
      endpoint: "/api/auth/logout",
      method: "POST",
      description: "User logout",
      category: "auth",
      payload: {},
      response: { success: "boolean" }
    },
    {
      endpoint: "/api/profiles/me",
      method: "GET",
      description: "Get current user profile",
      category: "profile",
      response: { id: "uuid", name: "string", bio: "string", interests: "array", gender: "string" }
    },
    {
      endpoint: "/api/profiles/:id",
      method: "GET",
      description: "Get user profile by ID",
      category: "profile",
      response: { id: "uuid", name: "string", bio: "string", interests: "array" }
    },
    {
      endpoint: "/api/profiles/me",
      method: "PUT",
      description: "Update current user profile",
      category: "profile",
      payload: { bio: "string", interests: "array" },
      response: { success: "boolean", profile: "UserProfile" }
    },
    {
      endpoint: "/api/matches",
      method: "GET",
      description: "Get user matches",
      category: "matching",
      response: { matches: "array<Match>", total: "number" }
    },
    {
      endpoint: "/api/likes",
      method: "POST",
      description: "Like a user",
      category: "matching",
      payload: { targetUserId: "uuid" },
      response: { match: "boolean", matchId: "uuid?" }
    },
    {
      endpoint: "/api/messages",
      method: "GET",
      description: "Get conversation messages",
      category: "messaging",
      params: { matchId: "uuid", limit: "number", offset: "number" },
      response: { messages: "array<Message>", total: "number" }
    },
    {
      endpoint: "/api/messages",
      method: "POST",
      description: "Send message",
      category: "messaging",
      payload: { matchId: "uuid", content: "string", type: "text|emoticon" },
      response: { message: "Message", success: "boolean" }
    },
    {
      endpoint: "/api/reactions",
      method: "POST",
      description: "Add message reaction",
      category: "messaging",
      payload: { messageId: "uuid", emoji: "string" },
      response: { reaction: "Reaction", success: "boolean" }
    },
    {
      endpoint: "/api/reactions/:id",
      method: "DELETE",
      description: "Remove message reaction",
      category: "messaging",
      response: { success: "boolean" }
    }
  ];
}

function formatTextOutput(systemInfo) {
  let output = "# TribeVibe System Overview\n\n";

  if (systemInfo.pages) {
    output += "## Pages\n";
    systemInfo.pages.forEach(page => {
      output += `- **${page.name}** (${page.route}): ${page.description}\n`;
    });
    output += "\n";
  }

  if (systemInfo.features) {
    output += "## Features\n";
    systemInfo.features.forEach(feature => {
      output += `- **${feature.name}**: ${feature.description}\n`;
      feature.actions.forEach(action => {
        output += `  - ${action.action}\n`;
      });
    });
    output += "\n";
  }

  if (systemInfo.apiEndpoints) {
    output += "## API Endpoints\n";
    systemInfo.apiEndpoints.forEach(endpoint => {
      output += `- **${endpoint.method}** ${endpoint.endpoint}: ${endpoint.description}\n`;
    });
  }

  return output;
}
```

## Output Format

### JSON Output (Default)
```json
{
  "ok": true,
  "type": "all",
  "timestamp": "2025-09-26T10:30:00.000Z",
  "systemInfo": {
    "pages": [
      {
        "name": "login",
        "route": "/auth/login",
        "description": "User authentication page",
        "type": "auth",
        "selectors": {
          "form": "form#login, .login-form",
          "emailInput": "input[name='email'], input[type='email']",
          "passwordInput": "input[name='password'], input[type='password']",
          "submitButton": "button[type='submit'], .btn-login"
        }
      }
    ],
    "features": [
      {
        "name": "like",
        "description": "Like other users to create potential matches",
        "category": "matching",
        "actions": [
          {
            "action": "click like button",
            "selector": ".btn-like, [data-action='like']"
          }
        ],
        "relatedPages": ["discover", "profile-detail"]
      }
    ],
    "apiEndpoints": [
      {
        "endpoint": "/api/auth/login",
        "method": "POST",
        "description": "User authentication",
        "category": "auth",
        "payload": { "email": "string", "password": "string" },
        "response": { "token": "jwt", "user": "UserProfile" }
      }
    ]
  }
}
```

### Text Output
```markdown
# TribeVibe System Overview

## Pages
- **login** (/auth/login): User authentication page
- **register** (/auth/register): User registration page
- **profile** (/profile): Current user profile management

## Features
- **like**: Like other users to create potential matches
  - click like button
  - create potential match
- **chat**: Send and receive messages with matches
  - send message
  - view conversation history

## API Endpoints
- **POST** /api/auth/login: User authentication
- **GET** /api/profiles/me: Get current user profile
- **POST** /api/messages: Send message
```

## Usage Examples

### Get All System Information
```bash
/system-discovery
```

### Get Only Pages Information
```bash
/system-discovery --type=pages
```

### Get Features in Text Format
```bash
/system-discovery --type=features --output=text
```

### Get API Endpoints Only
```bash
/system-discovery --type=api --output=json
```

## Integration

This command is designed to be called by:
- `/ui-frontend-agent` for system overview tasks
- `/orchestrator` when planning UI testing workflows
- Direct execution for documentation and reference

The system discovery provides essential information for:
- UI test planning and selector discovery
- Feature documentation and onboarding
- API endpoint mapping for integration testing
- Development reference and system understanding