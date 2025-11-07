# 🚨 CRITICAL: Process Management Safety Rules

**These rules apply to ALL agents that use the Bash tool.**

## ❌ **NEVER Kill Node.js Processes**

Claude Code itself runs on Node.js. Killing Node processes will **terminate the agent mid-execution** and corrupt the session.

### Forbidden Commands:
```bash
# ❌ NEVER USE THESE:
pkill -f node              # Kills Claude Code!
pkill node                 # Kills Claude Code!
killall node               # Kills Claude Code!
kill -9 $(pgrep node)      # Kills Claude Code!
kill -9 $(pidof node)      # Kills Claude Code!
ps aux | grep node | kill  # Kills Claude Code!
```

### Why This Is Critical:
- Claude Code runs on Node.js runtime
- The agent process itself is Node.js
- Killing Node processes = Killing yourself mid-task
- Results in:
  - ❌ Session corruption
  - ❌ Lost work/context
  - ❌ Incomplete operations
  - ❌ User frustration

## ✅ **Safe Process Management**

### Stopping Servers/Services:
```bash
# ✅ SAFE - Use service-specific commands:
npm stop                           # Stop npm scripts
docker-compose down                # Stop Docker containers
systemctl stop service-name        # Stop systemd services
./scripts/stop-server.sh           # Project-specific stop scripts

# ✅ SAFE - Stop specific PIDs (NOT node):
kill <specific-pid>                # Only if you know exact non-Node PID
kill $(cat /var/run/myapp.pid)     # Using PID files
```

### Finding Running Processes:
```bash
# ✅ SAFE - Check what's running:
ps aux | grep -v "node"            # List non-Node processes
lsof -i :3000                      # Find process on specific port
netstat -tulpn | grep :3000        # Alternative port check
docker ps                          # List containers
```

### Stopping Port Conflicts:
```bash
# ✅ SAFE - Kill process on specific port (NOT by name):
# 1. Find PID of process on port
PORT_PID=$(lsof -ti:3000)

# 2. Check it's NOT a Node process
ps -p $PORT_PID -o comm= | grep -v node

# 3. Only kill if NOT Node
if [ "$(ps -p $PORT_PID -o comm=)" != "node" ]; then
  kill $PORT_PID
fi

# ✅ SAFER - Just use different port or docker-compose restart:
docker-compose restart
```

## 🛡️ Safety Checklist

Before running any `kill` command, ask:
1. ✅ Am I killing a specific PID (not by process name)?
2. ✅ Have I verified it's NOT a Node process?
3. ✅ Is there a service-specific stop command I should use instead?
4. ✅ Could this affect Claude Code's runtime?

**When in doubt, DON'T kill - use service management commands instead.**

## Emergency Recovery

If you accidentally kill Node/Claude Code:
1. User will need to restart Claude Code session
2. All context will be lost
3. Work since last commit may be lost
4. User will be frustrated

**Prevention is critical - NEVER use process kill commands on Node.**
