# J.A.R.V.I.S. Personal AI Ecosystem
### Cinematic AI Interface + Voice Assistant + Full Windows Desktop Agency

Inspired by Tony Stark's artificial intelligence assistant in *Iron Man*, **J.A.R.V.I.S.** (Just A Rather Very Intelligent System) is a complete personal AI ecosystem built specifically for Windows. It provides natural voice interaction, an interactive Three.js 3D WebGL holographic Arc Reactor core, real-time tool orchestration, local desktop automation with full system access, multi-step task execution, and persistent memory.

---

## Subsystem Architecture

J.A.R.V.I.S. consists of three integrated components running cooperatively on your local machine:

1. **Cinematic Web Application (Port 5173 / Port 8000 Unified)**:
   - React 19, TypeScript, Tailwind CSS, Lucide Icons, Three.js WebGL, and Framer Motion.
   - Central reactive 3D holographic Arc Reactor core reacting dynamically to real assistant states: *Idle*, *Listening*, *Speech Recognition*, *Understanding*, *Planning*, *Executing*, *Speaking*, *Awaiting Approval*, *Success*, and *Error*.
   - Live listening indicator, FFT audio visualizer, real-time interim transcription, and British speech synthesis with interruption support.
   - 6 Core Screens: **Command Center**, **Dialogue Matrix**, **Capabilities & Tool Registry**, **Memory Vault**, **Windows Desktop Controller**, and **System Settings**.
   - Dual-serving mode: Accessible either on Vite (`http://localhost:5173`) or served directly by FastAPI (`http://127.0.0.1:8000`).

2. **AI Core Backend (Port 8000)**:
   - Python 3.13, FastAPI, SQLAlchemy 2.0 Async, aiosqlite, and Google GenAI SDK.
   - **Zero-Latency Fast-Path Reflex Router**: Executes immediate desktop actions, app launches, volume calibration, and Spotify playback in <15ms without external LLM network latency.
   - **Multi-Step Task Execution Planner**: Automatically decomposes compound commands into discrete, verifiable sequential steps (e.g. *"Open Spotify, play my study playlist, and minimize the window"*).
   - **Multi-LLM Provider Support**:
     - **Google Gemini**: Official `google-genai` SDK (`gemini-2.5-flash`, `gemini-2.0-flash`).
     - **Groq & OpenAI**: Free fast cloud inference (`llama-3.3-70b-versatile`, `gpt-4o-mini`).
     - **Offline Neural Fallback**: Works 100% offline out-of-the-box with Tony Stark persona and zero API key requirement.

3. **Windows Desktop Agent (Port 8001)**:
   - Local Python service secured with Bearer token authentication on loopback (`127.0.0.1:8001`).
   - **Spotify Player Engine**: Automatic metadata enrichment, URI protocol dispatch, window foregrounding, and active audio peak verification via Windows CoreAudio sessions.
   - **WhatsApp Automation Engine**: Direct message dispatch with contact name lookup, Unicode text pasting, and approval policy enforcement.
   - **Universal App Launcher & Window Manager**: Foreground activation of already-running apps (prevents duplicate instances), window state controls (*minimize*, *maximize*, *restore*, *close*).
   - **Audio & Media Controller**: Exact master volume calibration (`0-100%`) via `pycaw` and hardware virtual media keys (*play/pause*, *next*, *previous*, *stop*).
   - **File Manager & Local Search**: Known folders API (*Documents*, *Downloads*, *Desktop*, *Pictures*, *Music*, *Videos*), extension/size filters, recency sorting, and safe Recycle Bin deletion via `send2trash`.
   - **Desktop Companion HUD & System Tray**: Frameless draggable Arc Reactor widget with system tray minimization via `pystray` and optional Windows Startup configuration.

---

## How to Open and Use J.A.R.V.I.S.

### Method 1: Desktop Shortcut (Easiest)
Double-click the **`JARVIS`** shortcut on your Windows Desktop.

### Method 2: Double-Click Batch Launcher
In File Explorer, double-click:
- **`START_JARVIS.bat`** (or `JARVIS.bat`)

This automated launcher will:
1. Clear any stuck port listeners (8000, 8001, 5173).
2. Validate Python virtual environment and dependencies.
3. Start the Desktop Agent (8001) and AI Backend Core (8000).
4. Perform an active health check loop until all subsystems report 200 OK.
5. Launch the Frontend interface and open your default browser to J.A.R.V.I.S.

### Method 3: Python Runner
```powershell
.\.venv\Scripts\python.exe run_jarvis.py
```

### Method 4: Clean Shutdown
To shut down all active J.A.R.V.I.S. subsystems and free up all ports:
- Double-click **`STOP_JARVIS.bat`**
- Or run `.\stop_jarvis.ps1` in PowerShell.

---

## Directives & Natural Commands

You can speak or type to J.A.R.V.I.S. naturally in English or conversational Tamil:

| Category | Example Directive | What J.A.R.V.I.S. Does |
|---|---|---|
| **Spotify Music** | *"Play Believer by Imagine Dragons"* | Resolves metadata, activates Spotify, starts playback, verifies audio |
| **Spotify Music** | *"Play Arabic Kuthu on Spotify"* | Dispatches track query and triggers playback |
| **Spotify Playlist**| *"Play my workout playlist"* | Opens playlist in Spotify and initiates stream |
| **Media Transport** | *"Pause"* / *"Resume"* / *"Skip this song"* | Dispatches hardware media key directives |
| **System Audio** | *"Turn the volume down to 30 percent"* | Calibrates master Windows volume to exactly 30% |
| **System Audio** | *"Volume up"* / *"Mute audio"* | Increments volume or engages master mute |
| **WhatsApp** | *"Send 'I'll be there in ten minutes' to Ahmed on WhatsApp"* | Focuses WhatsApp, finds Ahmed, composes and sends |
| **Tamil Phrasing** | *"WhatsApp open pannu"* / *"Spotify open pannu"* | Natural conversational app launching |
| **Multi-Step** | *"Open Spotify, play my study playlist, and minimize the window"* | Executes 3-step sequential plan with per-step check |
| **File Operations**| *"Create a folder named College Projects in Documents"* | Creates directory in Windows Documents folder |
| **File Search** | *"Find my project report in Downloads"* | Searches Downloads for report files ranked by recency |
| **File Search** | *"Find every PDF containing cybersecurity in its filename"* | Scans directory with `.pdf` and keyword filters |
| **Visual Telemetry**| *"Find my latest screenshot and open it"* | Locates newest PNG screenshot and opens in viewer |
| **Window State** | *"Minimize Spotify"* / *"Maximize Chrome"* | Adjusts active application window state |
| **App Launcher** | *"Open VS Code and launch my JARVIS project"* | Activates or launches VS Code with project directory |
| **System Control** | *"Lock my PC"* | Engages Windows workstation security lock |
| **Diagnostics** | *"Check system status"* | Reports real CPU %, RAM %, Disk, Battery, and Uptime |

---

## Environment & Configuration

Configuration can be set via `.env` in the `backend/` directory or interactively in the **Settings** view in the UI.

| Key | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `gemini` / `openai` / `mock` | Primary AI provider (`gemini`, `openai`, `mock`) |
| `AI_MODEL` | `gemini-2.5-flash` | Model identifier |
| `GEMINI_API_KEY` | *(empty)* | Google Gemini API Key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Supported Google Gemini model |
| `OPENAI_API_KEY` | *(empty)* | Optional OpenAI or Groq key |
| `SPOTIFY_CLIENT_ID`| *(empty)* | Optional Spotify Developer App Client ID |
| `SPOTIFY_CLIENT_SECRET`| *(empty)* | Optional Spotify Developer App Client Secret |
| `BACKEND_PORT` | `8000` | Port for AI Core FastAPI service |
| `DESKTOP_AGENT_URL`| `http://127.0.0.1:8001` | Loopback address for Windows Agent |
| `DESKTOP_AGENT_TOKEN`| *(secret token)* | Bearer authentication secret |

> [!TIP]
> **No API Key required!** J.A.R.V.I.S. works fully offline with its local reflex engine. Every Windows desktop tool (Spotify playback, WhatsApp, volume control, file search, app launching, window management, screenshot, workstation lock) executes locally in <15ms. For open-domain reasoning, simply add a free Google Gemini key or Groq key.

---

## Verification & Automated Test Suite

Run the full automated test suite:
```powershell
.\.venv\Scripts\pytest backend\tests desktop_agent\tests
```

**Test Results Summary**:
- **49 passed in 47.17s (100% pass rate across 7 test suites)**:
  - `backend/tests/test_windows_integration.py` (15 tests): Verified 20-point Windows agency checklist.
  - `backend/tests/test_jarvis_advanced.py` (8 tests): Verified multi-step planner, Tamil directives, Spotify intents, exact volume %, and file operations.
  - `backend/tests/test_real_jarvis.py` (5 tests): Verified fast-path reflex routing, lore, and tool dispatch.
  - `backend/tests/test_tools.py` (7 tests): Verified calculator, status, web search, and file tools.
  - `backend/tests/test_auth.py` (3 tests): Verified JWT tokens and password authentication.
  - `backend/tests/test_chat_and_memory.py` (3 tests): Verified conversation logging and memory vault.
  - `backend/tests/test_health.py` (2 tests): Verified health endpoints and SPA serving.
  - `desktop_agent/tests/test_desktop_agent.py` (6 tests): Verified Bearer auth, URL validation, and telemetry.
#   J A R V I S  
 