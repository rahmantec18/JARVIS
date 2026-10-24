import os
import sys
import time
import signal
import subprocess
import webbrowser
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
VENV_PYTHON = ROOT_DIR / ".venv" / "Scripts" / "python.exe"

if not VENV_PYTHON.is_file():
    VENV_PYTHON = Path(sys.executable)

subprocesses = []


def cleanup(signum=None, frame=None):
    print("\n[!] Shutting down J.A.R.V.I.S. subsystems...")
    for proc in subprocesses:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    print("[✓] All subsystems shut down cleanly.")
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def main():
    print("=" * 60)
    print("       J.A.R.V.I.S. PERSONAL AI ECOSYSTEM - PYTHON RUNNER")
    print("=" * 60)
    os.chdir(ROOT_DIR)

    # 1. Start Desktop Agent
    print("[+] Launching Windows Desktop Agent (Port 8001)...")
    agent_proc = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "uvicorn", "desktop_agent.app.main:app", "--host", "127.0.0.1", "--port", "8001"],
        cwd=str(ROOT_DIR)
    )
    subprocesses.append(agent_proc)

    # 2. Start Backend Engine
    print("[+] Launching AI Backend Engine (Port 8000)...")
    backend_proc = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(ROOT_DIR / "backend")
    )
    subprocesses.append(backend_proc)

    # 3. Start Frontend (Vite)
    print("[+] Launching Frontend (Port 5173)...")
    frontend_proc = subprocess.Popen(
        "npm --prefix frontend run dev",
        shell=True,
        cwd=str(ROOT_DIR)
    )
    subprocesses.append(frontend_proc)

    # Wait for frontend or backend to be reachable (fast 200ms loop)
    print("[*] Synchronizing neural interface (http://127.0.0.1:5173 / :8000)...")
    frontend_ready = False
    backend_ready = False
    for i in range(25):
        time.sleep(0.2)
        if not frontend_ready:
            try:
                req = urllib.request.Request("http://127.0.0.1:5173")
                with urllib.request.urlopen(req, timeout=0.8) as resp:
                    if resp.status == 200:
                        frontend_ready = True
            except Exception:
                pass
        if not backend_ready:
            try:
                req = urllib.request.Request("http://127.0.0.1:8000/api/health")
                with urllib.request.urlopen(req, timeout=0.8) as resp:
                    if resp.status == 200:
                        backend_ready = True
            except Exception:
                pass

        if frontend_ready or (backend_ready and i >= 8):
            break

    launch_url = "http://127.0.0.1:5173" if frontend_ready else "http://127.0.0.1:8000"

    # Open Browser (Website Opens First)
    print(f"[✓] Subsystems online. Opening J.A.R.V.I.S. Command Center at {launch_url}...")
    webbrowser.open(launch_url)

    print("\n[✓] J.A.R.V.I.S. Active. Press Ctrl+C to terminate all services.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
