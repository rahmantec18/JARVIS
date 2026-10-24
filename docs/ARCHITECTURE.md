# J.A.R.V.I.S. Architecture Documentation

## System Architecture Overview

The J.A.R.V.I.S. Personal AI Ecosystem is architected into three coordinated subsystems connected over secure local loopback channels:

```
+--------------------------------------------------------------------------+
|                     1. Cinematic Frontend Web App                       |
|           (React 19, TypeScript, Tailwind CSS, Three.js WebGL)          |
|                                                                          |
|   +------------------------------------------------------------------+   |
|   |   3D Reactive AI Core (Concentric Rings, Energy Sphere, Galaxy)  |   |
|   +------------------------------------------------------------------+   |
|   | Command Center | Dialogue | Capabilities | Memory | Desktop | Config |
|   +------------------------------------------------------------------+   |
|   | Voice Engine: Web Speech Recognition + SpeechSynthesis Utterance |   |
+--------------------------------------------------------------------------+
                                     |
               HTTP / SSE / REST     |  (127.0.0.1:8000)
                                     v
+--------------------------------------------------------------------------+
|                       2. AI Core Backend (FastAPI)                      |
|                                                                          |
|   +------------------------------------------------------------------+   |
|   | Provider Layer: OpenAI SDK, Local Compatible (Ollama), Fallback  |   |
|   +------------------------------------------------------------------+   |
|   | Tool Execution Engine: Calculator, System Status, Web Search     |   |
|   +------------------------------------------------------------------+   |
|   | SQLite Persistent DB: Conversations, Messages, Memory Vault      |   |
+--------------------------------------------------------------------------+
                                     |
             Local Loopback Auth     |  (127.0.0.1:8001, Bearer Token)
                                     v
+--------------------------------------------------------------------------+
|                 3. Windows Desktop Agent (FastAPI Service)              |
|                                                                          |
|   +------------------------------------------------------------------+   |
|   | App Launcher (Strict Allowlist: notepad, calc, explorer, code)   |   |
|   +------------------------------------------------------------------+   |
|   | Sandbox File I/O: Path Traversal Defense, Directory Isolation    |   |
|   +------------------------------------------------------------------+   |
|   | System Telemetry: Hardware Sensors (CPU, RAM, Disk, Battery)    |   |
|   +------------------------------------------------------------------+   |
|   | Native Windows Notifications (System.Windows.Forms)              |   |
|   +------------------------------------------------------------------+   |
|   | Security Interlock: Interactive User Confirmation Queue          |   |
+--------------------------------------------------------------------------+
```

## 1. Frontend Subsystem
- **Framework**: Vite 8 + React 19 + TypeScript.
- **Visual Engine**: Three.js WebGL rendering a multi-layered holographic reactor with rotating concentric gimbal rings, particle galaxies, audio-reactive sphere displacement, and cursor parallax tracking.
- **State System**: Dynamically transitions between `idle`, `listening`, `processing`, `thinking`, `speaking`, `executing_tool`, `awaiting_approval`, `success`, and `error`.
- **Acoustic Layer**: Real-time microphone listening, FFT audio analysis, and configurable SpeechSynthesis with speed and pitch control.

## 2. AI Core Backend
- **Framework**: Python 3.13 + FastAPI + SQLAlchemy Async + aiosqlite.
- **Provider Abstraction**: Allows hot-swapping between official OpenAI, OpenAI-compatible local endpoints (Ollama, LM Studio, vLLM), or the built-in smart J.A.R.V.I.S. persona fallback.
- **Tool Registry**: Declares JSON-schema function definitions, validates incoming arguments, and enforces permission checks.
- **Database**: Asynchronous SQLite database storing persistent memories, conversation histories, tasks, and audit logs.

## 3. Windows Desktop Agent
- **Bound Interface**: Exclusively binds to `127.0.0.1:8001` to prevent exposure to external networks.
- **Authentication**: All endpoints require an authorization Bearer token.
- **Allowlist Enforcement**: Applications are strictly validated against an approved dictionary before process execution.
- **Path Isolation**: Directory access is restricted to verified user folders with symlink and traversal checks.
- **Security Interlocks**: Irreversible actions require an explicit confirmation token generated on the server and authorized in the UI.
