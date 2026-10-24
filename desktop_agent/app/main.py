import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from desktop_agent.security.authorizer import authorizer
from desktop_agent.tools.app_launcher import (
    launch_application, launch_custom_app, open_browser_url,
    activate_application_window, set_window_state
)
from desktop_agent.tools.system_telemetry import get_desktop_system_info
from desktop_agent.tools.notifier import show_notification
from desktop_agent.tools.file_manager import (
    search_files, read_file, write_file, write_note,
    list_directory, reveal_in_explorer, delete_item,
    create_directory, rename_item, copy_item, move_item
)
from desktop_agent.tools.command_runner import execute_powershell
from desktop_agent.tools.media_controller import control_volume, control_media, lock_workstation, open_windows_settings
from desktop_agent.tools.spotify_player import play_spotify, pause_spotify, resume_spotify, skip_spotify, previous_spotify
from desktop_agent.tools.screen_capture import capture_screenshot
from desktop_agent.tools.clipboard_manager import get_clipboard, set_clipboard
from desktop_agent.tools.process_controller import list_processes, kill_process
from desktop_agent.tools.whatsapp_automation import send_whatsapp_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [JARVIS Desktop]: %(message)s")
logger = logging.getLogger("jarvis.desktop_agent")

app = FastAPI(
    title="J.A.R.V.I.S. Windows Desktop Agent",
    description="Controlled Local Desktop Automation Service",
    version="1.0.0"
)

# Loopback origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_desktop_auth(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorizer.verify_token(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized: invalid pairing token")
    return True


class ActionPayload(BaseModel):
    action: str
    parameters: Dict[str, Any] = {}
    confirmed: bool = False


class ApprovalResolution(BaseModel):
    approved: bool


@app.get("/health")
async def health():
    return {"status": "online", "service": "JARVIS Desktop Agent", "platform": "Windows"}


@app.get("/api/status", dependencies=[Depends(verify_desktop_auth)])
async def get_status():
    authorizer.reload()
    system_info = get_desktop_system_info()
    apps_data = [
        {"id": k, "name": v["name"], "description": v["description"], "requires_approval": v.get("requires_approval", False)}
        for k, v in authorizer.config.get("approved_apps", {}).items()
    ]
    return {
        "status": "connected",
        "system_info": system_info,
        "approved_apps": apps_data,
        "allowed_directories": authorizer.config.get("allowed_directories", []),
        "pending_approvals": len(authorizer.pending_approvals),
        "full_access_mode": authorizer.config.get("full_access_mode", True)
    }


@app.post("/api/action", dependencies=[Depends(verify_desktop_auth)])
async def execute_action(payload: ActionPayload):
    action = payload.action.lower().strip()
    params = payload.parameters
    confirmed = payload.confirmed

    logger.info(f"Received desktop action request: {action} (confirmed={confirmed})")

    # App Launching
    if action in ["launch_hud", "start_hud", "open_hud", "companion_hud"]:
        import subprocess
        from pathlib import Path
        repo_root = Path(__file__).resolve().parent.parent.parent
        pythonw = repo_root / ".venv" / "Scripts" / "pythonw.exe"
        if not pythonw.exists():
            pythonw = repo_root / ".venv" / "Scripts" / "python.exe"
        hud_script = repo_root / "desktop_companion.py"
        subprocess.Popen([str(pythonw), str(hud_script)], cwd=str(repo_root))
        return {
            "success": True,
            "message": "J.A.R.V.I.S. Floating Companion HUD launched successfully on desktop."
        }

    elif action == "launch_app":
        app_id = params.get("app_id", "")
        return launch_application(app_id, confirmed=confirmed)

    elif action in ["launch_custom_app", "open_program"]:
        target = params.get("target") or params.get("app") or params.get("path", "")
        args = params.get("arguments", [])
        return launch_custom_app(target, args)

    elif action == "open_url":
        url = params.get("url", "")
        browser = params.get("browser")
        return open_browser_url(url, browser=browser, confirmed=confirmed)

    elif action in ["send_whatsapp", "whatsapp_message"]:
        contact = params.get("contact", "")
        text = params.get("text") or params.get("message", "Hi")
        return send_whatsapp_message(contact=contact, text=text)

    # Shell Execution
    elif action in ["run_command", "run_powershell", "execute_command"]:
        cmd = params.get("command") or params.get("cmd", "")
        timeout = params.get("timeout", 20)
        return execute_powershell(cmd, timeout=timeout)

    # Hardware & Media Controls
    elif action == "control_volume":
        vol_action = params.get("action", "up")
        level = params.get("level")
        return control_volume(vol_action, level)

    elif action == "control_media":
        media_action = params.get("action", "play_pause")
        return control_media(media_action)

    elif action in ["play_spotify", "spotify_play"]:
        query = params.get("query") or params.get("song") or params.get("track", "")
        playlist = params.get("playlist", False)
        return play_spotify(query=query, playlist=playlist)

    elif action in ["pause_spotify", "spotify_pause"]:
        return pause_spotify()

    elif action in ["resume_spotify", "spotify_resume"]:
        return resume_spotify()

    elif action in ["skip_spotify", "spotify_skip", "next_spotify"]:
        return skip_spotify()

    elif action in ["previous_spotify", "spotify_previous", "prev_spotify"]:
        return previous_spotify()

    elif action in ["activate_window", "focus_window"]:
        target = params.get("target") or params.get("name") or params.get("app", "")
        return activate_application_window(target)

    elif action in ["set_window_state", "window_state"]:
        target = params.get("target") or params.get("name") or params.get("app", "")
        state = params.get("state", "minimize")
        return set_window_state(target, state)

    elif action in ["take_screenshot", "capture_screen", "screenshot"]:
        b64 = params.get("include_base64", False)
        return capture_screenshot(include_base64=b64)

    elif action == "lock_workstation":
        return lock_workstation()

    elif action == "open_settings":
        page = params.get("page", "")
        return open_windows_settings(page)

    # Clipboard
    elif action in ["get_clipboard", "clipboard_read"]:
        return get_clipboard()

    elif action in ["set_clipboard", "clipboard_write"]:
        text = params.get("text") or params.get("content", "")
        return set_clipboard(text)

    # Process Management
    elif action == "list_processes":
        f_name = params.get("filter_name") or params.get("filter")
        limit = params.get("limit", 25)
        return list_processes(filter_name=f_name, limit=limit)

    elif action == "kill_process":
        target = params.get("target") or params.get("pid") or params.get("name", "")
        return kill_process(target)

    # File Operations
    elif action == "search_files":
        query = params.get("query", "")
        base_dir = params.get("base_dir", "C:\\Users\\abdur\\OneDrive\\Documents\\JARVIS")
        return search_files(query, base_dir)

    elif action == "read_file":
        file_path = params.get("file_path", "")
        max_chars = params.get("max_chars", 8000)
        return read_file(file_path, max_chars)

    elif action == "write_file":
        file_path = params.get("file_path", "")
        content = params.get("content", "")
        return write_file(file_path, content)

    elif action == "create_note":
        title = params.get("title", "Note")
        content = params.get("content", "")
        folder = params.get("folder", "notes")
        return write_note(title, content, folder)

    elif action == "list_directory":
        dir_path = params.get("dir_path") or params.get("path", ".")
        return list_directory(dir_path)

    elif action == "reveal_file":
        target_path = params.get("path") or params.get("target_path", ".")
        return reveal_in_explorer(target_path)

    elif action in ["create_directory", "create_folder", "make_folder"]:
        name = params.get("folder_name") or params.get("name") or params.get("folder", "New Folder")
        parent = params.get("parent_folder") or params.get("parent") or params.get("in", "documents")
        return create_directory(name, parent)

    elif action in ["rename_item", "rename_file", "rename_folder"]:
        src = params.get("src") or params.get("path") or params.get("old_name", "")
        new_name = params.get("new_name") or params.get("name") or params.get("dst", "")
        return rename_item(src, new_name)

    elif action in ["copy_item", "copy_file", "copy_folder"]:
        src = params.get("src") or params.get("path") or params.get("source", "")
        dst = params.get("dst") or params.get("destination", "")
        return copy_item(src, dst)

    elif action in ["move_item", "move_file", "move_folder"]:
        src = params.get("src") or params.get("path") or params.get("source", "")
        dst = params.get("dst") or params.get("destination", "")
        return move_item(src, dst)

    elif action in ["delete_item", "delete_file", "delete_folder", "remove_item", "remove_file", "delete"]:
        target = params.get("target") or params.get("file_path") or params.get("path") or params.get("name", "")
        return delete_item(target)

    # Telemetry & Notifications
    elif action == "system_info":
        return {"success": True, "data": get_desktop_system_info()}

    elif action == "notify":
        title = params.get("title", "J.A.R.V.I.S.")
        message = params.get("message", "")
        return show_notification(title, message)

    else:
        return {
            "success": False,
            "error": f"Unknown or unsupported desktop action: '{action}'."
        }


@app.post("/api/approve/{approval_id}", dependencies=[Depends(verify_desktop_auth)])
async def handle_approval(approval_id: str, res: ApprovalResolution):
    record = authorizer.resolve_approval(approval_id, res.approved)
    if not record:
        raise HTTPException(status_code=404, detail="Approval request expired or not found.")

    if not res.approved:
        return {"status": "rejected", "message": "Action cancelled by user."}

    # Execute approved action with confirmed=True
    return await execute_action(ActionPayload(
        action=record["action"],
        parameters=record["parameters"],
        confirmed=True
    ))


if __name__ == "__main__":
    import uvicorn
    cfg = authorizer.config
    uvicorn.run("desktop_agent.app.main:app", host=cfg.get("host", "127.0.0.1"), port=cfg.get("port", 8001), reload=True)
