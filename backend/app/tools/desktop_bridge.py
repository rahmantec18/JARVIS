import httpx
from typing import Dict, Any, Optional, List
from app.core.config import settings


async def call_desktop_agent(action: str, parameters: Dict[str, Any] = None, confirmed: bool = False) -> Dict[str, Any]:
    """Communicate securely with the local Windows Desktop Agent over loopback."""
    if not settings.DESKTOP_AGENT_ENABLED:
        return {
            "success": False,
            "error": "Windows Desktop Agent is disabled in configuration.",
            "requires_desktop_agent": True
        }

    url = f"{settings.DESKTOP_AGENT_URL.rstrip('/')}/api/action"
    headers = {
        "Authorization": f"Bearer {settings.DESKTOP_AGENT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "action": action,
        "parameters": parameters or {},
        "confirmed": confirmed
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=2.0)) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 401:
                return {
                    "success": False,
                    "error": "Authentication failed with local Desktop Agent (invalid token)."
                }
            elif resp.status_code == 403:
                return resp.json()
            else:
                return {
                    "success": False,
                    "error": f"Desktop Agent returned HTTP {resp.status_code}: {resp.text}"
                }
    except (httpx.ConnectError, Exception) as e:
        # Fallback to direct local tool execution if desktop agent service on 8001 is offline
        try:
            return _execute_local_desktop_action(action, parameters or {}, confirmed)
        except Exception as local_err:
            return {
                "success": False,
                "error": f"Failed to communicate with Desktop Agent: {str(e)} (Local fallback: {str(local_err)})",
                "offline": True
            }


def _execute_local_desktop_action(action: str, parameters: Dict[str, Any], confirmed: bool = False) -> Dict[str, Any]:
    act = action.lower().strip()
    if act == "launch_app":
        from desktop_agent.tools.app_launcher import launch_application
        return launch_application(parameters.get("app_id", ""), confirmed=confirmed)
    elif act in ["launch_custom_app", "open_program"]:
        from desktop_agent.tools.app_launcher import launch_custom_app
        return launch_custom_app(parameters.get("target") or parameters.get("app") or parameters.get("path", ""), parameters.get("arguments", []))
    elif act == "open_url":
        from desktop_agent.tools.app_launcher import open_browser_url
        return open_browser_url(parameters.get("url", ""), browser=parameters.get("browser"), confirmed=confirmed)
    elif act == "play_spotify":
        from desktop_agent.tools.spotify_player import play_spotify
        return play_spotify(parameters.get("query", ""), playlist=parameters.get("playlist", False))
    elif act == "pause_spotify":
        from desktop_agent.tools.spotify_player import pause_spotify
        return pause_spotify()
    elif act == "resume_spotify":
        from desktop_agent.tools.spotify_player import resume_spotify
        return resume_spotify()
    elif act == "skip_spotify":
        from desktop_agent.tools.spotify_player import skip_spotify
        return skip_spotify()
    elif act == "previous_spotify":
        from desktop_agent.tools.spotify_player import previous_spotify
        return previous_spotify()
    elif act == "control_volume":
        from desktop_agent.tools.media_controller import control_volume
        return control_volume(parameters.get("action", "up"), parameters.get("level"))
    elif act == "control_media":
        from desktop_agent.tools.media_controller import control_media
        return control_media(parameters.get("action", "play"))
    elif act == "set_window_state":
        from desktop_agent.tools.app_launcher import set_window_state
        return set_window_state(parameters.get("target", ""), parameters.get("state", "minimize"))
    elif act in ["send_whatsapp", "whatsapp_message"]:
        from desktop_agent.tools.whatsapp import send_whatsapp_message
        return send_whatsapp_message(parameters.get("contact", ""), parameters.get("text") or parameters.get("message", "Hi"))
    raise NotImplementedError(f"Action '{act}' has no direct local handler")


async def open_approved_app(app_id: str, confirmed: bool = False) -> Dict[str, Any]:
    """Launch an allowlisted Windows desktop application."""
    return await call_desktop_agent("launch_app", {"app_id": app_id}, confirmed=confirmed)


async def open_website(url: str, browser: Optional[str] = None, confirmed: bool = False) -> Dict[str, Any]:
    """Open an approved website in the user's browser."""
    payload = {"url": url}
    if browser:
        payload["browser"] = browser
    return await call_desktop_agent("open_url", payload, confirmed=confirmed)


async def launch_custom_application(target: str) -> Dict[str, Any]:
    """Launch any application or document on the Windows system."""
    return await call_desktop_agent("launch_custom_app", {"target": target})


async def run_powershell_command(command: str) -> Dict[str, Any]:
    """Execute a PowerShell or Command Prompt instruction on Windows."""
    return await call_desktop_agent("run_command", {"command": command})


async def control_system_volume(action: str, level: Optional[int] = None) -> Dict[str, Any]:
    """Control system audio (set percentage, up, down, mute, unmute)."""
    return await call_desktop_agent("control_volume", {"action": action, "level": level})


async def control_media_playback(action: str) -> Dict[str, Any]:
    """Control system media playback (play, pause, next, previous, stop)."""
    return await call_desktop_agent("control_media", {"action": action})


async def play_spotify_music(query: str, playlist: bool = False) -> Dict[str, Any]:
    """Search and initiate playback for a song, artist, or playlist on Spotify."""
    return await call_desktop_agent("play_spotify", {"query": query, "playlist": playlist})


async def pause_spotify_music() -> Dict[str, Any]:
    """Pause playback on Spotify."""
    return await call_desktop_agent("pause_spotify", {})


async def resume_spotify_music() -> Dict[str, Any]:
    """Resume playback on Spotify."""
    return await call_desktop_agent("resume_spotify", {})


async def skip_spotify_track() -> Dict[str, Any]:
    """Skip to next track on Spotify."""
    return await call_desktop_agent("skip_spotify", {})


async def previous_spotify_track() -> Dict[str, Any]:
    """Return to previous track on Spotify."""
    return await call_desktop_agent("previous_spotify", {})


async def activate_desktop_window(target: str) -> Dict[str, Any]:
    """Bring an application window to the foreground."""
    return await call_desktop_agent("activate_window", {"target": target})


async def set_desktop_window_state(target: str, state: str = "minimize") -> Dict[str, Any]:
    """Minimize, maximize, restore, or close an application window."""
    return await call_desktop_agent("set_window_state", {"target": target, "state": state})


async def capture_desktop_screenshot(include_base64: bool = False) -> Dict[str, Any]:
    """Capture full desktop screen to a PNG image file."""
    return await call_desktop_agent("take_screenshot", {"include_base64": include_base64})


async def read_system_clipboard() -> Dict[str, Any]:
    """Read text currently on the clipboard."""
    return await call_desktop_agent("get_clipboard", {})


async def write_system_clipboard(text: str) -> Dict[str, Any]:
    """Copy text string onto the clipboard."""
    return await call_desktop_agent("set_clipboard", {"text": text})


async def list_system_processes(filter_name: Optional[str] = None) -> Dict[str, Any]:
    """List active processes running on the machine."""
    return await call_desktop_agent("list_processes", {"filter_name": filter_name})


async def kill_system_process(target: str) -> Dict[str, Any]:
    """Terminate a process by name or PID."""
    return await call_desktop_agent("kill_process", {"target": target})


async def lock_windows_workstation() -> Dict[str, Any]:
    """Lock the Windows desktop session."""
    return await call_desktop_agent("lock_workstation", {})


async def open_system_settings(page: str = "") -> Dict[str, Any]:
    """Open Windows modern Settings."""
    return await call_desktop_agent("open_settings", {"page": page})


async def write_system_file(file_path: str, content: str) -> Dict[str, Any]:
    """Write or overwrite content to any file on the machine."""
    return await call_desktop_agent("write_file", {"file_path": file_path, "content": content})


async def list_system_directory(path: str = ".") -> Dict[str, Any]:
    """List files in any folder."""
    return await call_desktop_agent("list_directory", {"path": path})


async def reveal_file_in_explorer(path: str) -> Dict[str, Any]:
    """Highlight file or folder in Windows Explorer."""
    return await call_desktop_agent("reveal_file", {"path": path})


async def send_whatsapp_message(contact: str = "", message: str = "Hi") -> Dict[str, Any]:
    """Send or prepare a WhatsApp message on Windows."""
    return await call_desktop_agent("send_whatsapp", {"contact": contact, "text": message})


async def delete_system_item(target: str) -> Dict[str, Any]:
    """Delete a file, directory, screenshot, note, or clear recycle bin/temp files."""
    return await call_desktop_agent("delete_item", {"target": target})


async def create_desktop_directory(folder_name: str, parent_folder: str = "documents") -> Dict[str, Any]:
    """Create a new folder in Documents, Desktop, or custom path."""
    return await call_desktop_agent("create_directory", {"folder_name": folder_name, "parent_folder": parent_folder})


async def rename_desktop_item(src: str, new_name: str) -> Dict[str, Any]:
    """Rename a file or folder."""
    return await call_desktop_agent("rename_item", {"src": src, "new_name": new_name})


async def copy_desktop_item(src: str, dst: str) -> Dict[str, Any]:
    """Copy a file or folder."""
    return await call_desktop_agent("copy_item", {"src": src, "dst": dst})


async def move_desktop_item(src: str, dst: str) -> Dict[str, Any]:
    """Move a file or folder."""
    return await call_desktop_agent("move_item", {"src": src, "dst": dst})


async def launch_companion_hud() -> Dict[str, Any]:
    """Launch the draggable always-on-top desktop companion HUD."""
    return await call_desktop_agent("launch_hud", {})

