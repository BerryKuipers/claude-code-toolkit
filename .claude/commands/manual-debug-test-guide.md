# 🧪 Manual Debug Command Testing Guide

## 🎯 Complete MCP Integration Testing Workflow

Your debug command is now **production-ready** with full MCP integration! Here's how to manually test all capabilities:

## 📋 **STEP 1: Run Pre-Test Validation**
```bash
# Verify all systems are ready
./.claude/commands/test-debug-mcp.sh
```

**✅ Expected Results:**
- ✅ Loki MCP server connected
- ✅ Chrome DevTools MCP server connected
- ✅ API server responding (npm run dev working)
- ✅ Context system loaded

---

## 🔧 **STEP 2: Test Backend Debugging (Works Now)**

### **Basic System Analysis**
```bash
/debug
```
**Expected:** Comprehensive system analysis using Loki MCP + fallback diagnostics

### **Targeted Log Analysis**
```bash
/debug logs api-main --last 30m
/debug logs authservice --last 1h
/debug database
```
**Expected:** Real-time Loki queries showing:
- Recent API activity with trace IDs
- Authentication events
- Database connection status

### **System Diagnostics**
```bash
/debug ports
/debug config
```
**Expected:** Port usage analysis and configuration validation

---

## 🌐 **STEP 3: Enable Chrome Remote Debugging**

**⚠️ Currently Required for Frontend Debugging:**
```bash
# Close all Chrome instances first
taskkill /f /im chrome.exe

# Start Chrome with remote debugging
chrome --remote-debugging-port=9222

# Or use Chrome Canary if available
chrome-canary --remote-debugging-port=9222
```

**🔍 Verify Chrome DevTools Connection:**
- Open: `http://localhost:9222/json/list`
- Should show available tabs for debugging

---

## 🎨 **STEP 4: Test Frontend Debugging (After Chrome Setup)**

### **Element Inspection**
```bash
/debug inspect .login-form
/debug inspect button[type="submit"]
/debug inspect .profile-card
```
**Expected:** Chrome DevTools MCP integration showing:
- Element properties and computed styles
- DOM structure analysis
- Accessibility information

### **Network Analysis**
```bash
/debug network xhr
/debug network fetch
/debug network errors
```
**Expected:** Real-time network monitoring:
- API request/response analysis
- Failed network requests
- Performance metrics

### **JavaScript Console**
```bash
/debug console 'window.location.href'
/debug console 'localStorage.getItem("authToken")'
/debug console 'document.querySelector(".profile-card")'
```
**Expected:** JavaScript execution results in browser context

### **Performance Profiling**
```bash
/debug profile cpu
/debug profile memory
/debug breakpoint src/components/ProfileCard.tsx:45
```
**Expected:** Performance analysis and debugging capabilities

---

## 🚀 **STEP 5: Test Orchestrator Integration**

### **Complex Multi-Command Workflows**
```bash
/debug logs api-main --last 30m
# → Should automatically delegate to orchestrator for follow-up analysis
# → Orchestrator may suggest related commands like /refactor or /test
```

**Expected Orchestrator Behavior:**
- ✅ Smart delegation to specialized commands
- ✅ Cross-command collaboration suggestions
- ✅ Advisory mode for background analysis
- ✅ Conflict resolution for competing recommendations

---

## 📊 **STEP 6: Test Fallback Modes**

### **Without Chrome DevTools (Current State)**
```bash
/debug inspect .login-form
```
**Expected Fallback:**
- Static code analysis of React components
- CSS selector validation
- Accessibility audit without live DOM

### **Without Loki MCP (Simulated)**
```bash
# Temporarily disable Loki MCP to test fallback
/debug logs api-main --last 30m
```
**Expected Fallback:**
- Local log file analysis
- System diagnostic alternatives
- Graceful degradation messages

---

## 🔄 **STEP 7: Test Command Memory & Context**

### **Persistent Context System**
The debug command automatically knows:
- ✅ Your `npm run dev` setup (no server restarts)
- ✅ Your admin role and preferences
- ✅ Build system status and timing
- ✅ Recent debugging history

### **Smart Suggestions**
```bash
/debug
# Should provide contextually relevant suggestions based on:
# - Recent errors in logs
# - Current development phase
# - Previous debugging sessions
```

---

## 🎯 **Expected Production Behaviors**

### **Intelligent Routing (Step 0)**
- **Frontend commands** (`inspect`, `network`, `console`) → Chrome DevTools MCP
- **Backend commands** (`logs`, `database`, `ports`) → Loki MCP + System Analysis
- **Hybrid commands** (`profile`, `breakpoint`) → Multiple MCP coordination

### **Graceful Degradation**
- **MCP available**: Full-featured debugging with real-time data
- **MCP unavailable**: Smart fallbacks with static analysis
- **Mixed availability**: Hybrid approach using available tools

### **Hub Integration**
- **Complex issues** → Automatic orchestrator delegation
- **Follow-up actions** → Smart command suggestions
- **Resource conflicts** → Coordinated resolution

---

## 🚨 **Troubleshooting Guide**

### **Chrome DevTools Not Working**
1. ✅ Chrome remote debugging enabled on port 9222?
2. ✅ Firewall blocking localhost:9222?
3. ✅ Multiple Chrome instances running?
4. ✅ Use Chrome Canary as alternative

### **Loki Integration Issues**
1. ✅ Grafana accessible at localhost:3000?
2. ✅ API key valid in MCP config?
3. ✅ Logs flowing to Loki (check Promtail)?
4. ✅ Service names matching in queries?

### **Context System Issues**
1. ✅ `.claude/context/global-state.json` exists?
2. ✅ Environment rules loaded correctly?
3. ✅ Architectural principles accessible?

---

## 🏆 **Success Metrics**

**✅ Backend Debugging:** Should work immediately with current setup
**✅ Loki Integration:** Real-time log queries with trace correlation
**✅ Orchestrator Delegation:** Smart follow-up command suggestions
**✅ Context Awareness:** No repeated setup questions
**✅ Fallback Modes:** Graceful degradation when MCP unavailable

**🎯 Frontend Debugging:** Requires Chrome remote debugging setup

Your debug command now provides **professional-grade debugging capabilities** with intelligent MCP integration and comprehensive fallback support! 🚀