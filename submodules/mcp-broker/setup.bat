@echo off
REM MCP Broker Setup Helper for Windows
REM This script helps you configure the MCP broker for Claude Code

setlocal enabledelayedexpansion

echo.
echo =========================================
echo    MCP Broker Setup Helper
echo =========================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "BROKER_JS=%SCRIPT_DIR%dist\broker.js"

echo [*] Detected broker location:
echo     %SCRIPT_DIR%
echo.

REM Check if built
if not exist "%BROKER_JS%" (
    echo [!] Broker not built yet
    echo.
    set /p BUILD="Would you like to build it now? (y/n): "
    if /i "!BUILD!"=="y" (
        echo [*] Installing dependencies...
        call npm install
        echo.
        echo [*] Building broker...
        call npm run build
        echo [+] Build complete!
        echo.
    ) else (
        echo [-] Cannot continue without building. Run: npm install && npm run build
        exit /b 1
    )
)

REM Check for config
if not exist "%SCRIPT_DIR%servers.config.json" (
    echo [!] servers.config.json not found
    echo.
    set /p CREATE="Would you like to create it from sample? (y/n): "
    if /i "!CREATE!"=="y" (
        copy "%SCRIPT_DIR%servers.config.sample.json" "%SCRIPT_DIR%servers.config.json" >nul
        echo [+] Created servers.config.json
        echo     Edit this file to add your MCP servers
        echo.
    )
)

REM Generate config snippet
echo [*] Claude Code Configuration:
echo.
echo Add this to your .claude.json file:
echo.

REM Convert path to Windows format with escaped backslashes
set "WINDOWS_PATH=%BROKER_JS:\=\\%"

echo {
echo   "mcpServers": {
echo     "broker": {
echo       "command": "node",
echo       "args": [
echo         "%WINDOWS_PATH%"
echo       ]
echo     }
echo   }
echo }
echo.
echo Location: C:\Users\YourUsername\.claude.json
echo.

echo [*] Next Steps:
echo.
echo 1. Edit servers.config.json to add your MCP servers
echo 2. Copy the configuration above to your .claude.json
echo 3. Restart Claude Code
echo 4. Use broker.search to discover available tools
echo.
echo [+] Setup helper complete!
echo.
echo For detailed documentation, see:
echo   - SETUP.md (comprehensive setup guide)
echo   - REFLECTIVE-MODE.md (dynamic tool discovery)
echo   - VAULT-SETUP.md (secure secret management)
echo.
pause
