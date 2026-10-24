import os
import glob
import subprocess
import shutil
import webbrowser
from pathlib import Path
from typing import Dict, Any, List, Optional
from desktop_agent.security.authorizer import authorizer


COMMON_APP_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"C:\Program Files\Mozilla Firefox\firefox.exe",
    r"C:\Users\abdur\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    r"C:\Users\abdur\AppData\Roaming\Spotify\Spotify.exe",
    r"C:\Users\abdur\AppData\Local\Discord\Update.exe",
    r"C:\Program Files (x86)\Steam\steam.exe",
    r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    r"C:\Windows\System32\notepad.exe",
    r"C:\Windows\System32\calc.exe",
    r"C:\Windows\explorer.exe",
    r"C:\Windows\System32\cmd.exe",
    r"C:\Windows\System32\taskmgr.exe",
    r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
]

PROTOCOL_MAP = {
    "whatsapp": ("whatsapp:", "https://web.whatsapp.com"),
    "telegram": ("tg://", "https://web.telegram.org"),
    "calculator": ("calculator:", None),
    "calc": ("calculator:", None),
    "settings": ("ms-settings:", None),
    "camera": ("microsoft.windows.camera:", None),
    "photos": ("ms-photos:", None),
    "store": ("ms-windows-store:", None),
    "clock": ("ms-clock:", None),
    "alarms": ("ms-clock:", None),
    "weather": ("bingweather:", None),
    "maps": ("bingmaps:", None),
    "spotify": ("spotify:", None),
    "edge": ("microsoft-edge:", None),
}

WEB_SHORTCUTS = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://www.github.com",
    "chatgpt": "https://chatgpt.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "reddit": "https://www.reddit.com",
    "linkedin": "https://www.linkedin.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
}

FOLDER_MAP = {
    "downloads": os.path.expanduser(r"~\Downloads"),
    "documents": os.path.expanduser(r"~\Documents"),
    "desktop": os.path.expanduser(r"~\Desktop"),
    "pictures": os.path.expanduser(r"~\Pictures"),
    "music": os.path.expanduser(r"~\Music"),
    "videos": os.path.expanduser(r"~\Videos"),
    "screenshots": str(Path(__file__).resolve().parent.parent.parent / "screenshots"),
    "notes": str(Path(__file__).resolve().parent.parent.parent / "notes"),
    "recycle bin": "shell:RecycleBinFolder",
    "trash": "shell:RecycleBinFolder",
}


def _find_start_menu_shortcut(name: str) -> Optional[str]:
    """Search Windows Start Menu shortcuts for installed applications."""
    clean = name.lower().strip()
    search_dirs = [
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs")
    ]
    
    # 1. Exact match .lnk
    for base in search_dirs:
        if not os.path.exists(base):
            continue
        for lnk in glob.glob(os.path.join(base, "**", "*.lnk"), recursive=True):
            base_name = os.path.splitext(os.path.basename(lnk))[0].lower()
            if base_name == clean:
                return lnk

    # 2. Substring match, filtering out uninstallers, help, and reset shortcuts
    candidates = []
    for base in search_dirs:
        if not os.path.exists(base):
            continue
        for lnk in glob.glob(os.path.join(base, "**", "*.lnk"), recursive=True):
            base_name = os.path.splitext(os.path.basename(lnk))[0].lower()
            if clean in base_name:
                is_bad = any(x in base_name for x in ["uninstall", "manual", "help", "documentation", "reset", "configur"])
                candidates.append((is_bad, len(base_name), lnk))

    if candidates:
        candidates.sort(key=lambda x: (x[0], x[1]))
        return candidates[0][2]

    return None


def _find_executable(name: str) -> Optional[str]:
    """Find executable on system path, common directories, or Start Menu."""
    clean = name.lower().strip()

    # 1. Direct which
    w = shutil.which(clean)
    if w:
        return w
    w = shutil.which(f"{clean}.exe")
    if w:
        return w

    # 2. Check common known paths
    for p in COMMON_APP_PATHS:
        if clean in os.path.basename(p).lower() and os.path.isfile(p):
            return p

    # 3. Check Start Menu shortcuts
    lnk = _find_start_menu_shortcut(clean)
    if lnk:
        return lnk

    return None


def _launch_target(target: str) -> bool:
    """Launch target via os.startfile or shell with fallback."""
    try:
        if hasattr(os, "startfile"):
            os.startfile(target)
            return True
    except Exception:
        pass

    try:
        subprocess.Popen(f'start "" "{target}"', shell=True)
        return True
    except Exception:
        pass

    try:
        subprocess.Popen([target], shell=False)
        return True
    except Exception:
        pass

    return False


def find_app_window(target_name: str) -> Optional[int]:
    """Find a visible top-level window matching the given application name or process."""
    clean = target_name.lower().strip()
    try:
        import win32gui
        import win32process
        import psutil

        candidates = []

        def enum_cb(hwnd, _):
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    p = psutil.Process(pid)
                    pname = p.name().lower()
                except Exception:
                    pname = ""

                # Match against process name or window title
                if clean in pname or (title and clean in title.lower()):
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    if width > 100 and height > 100:
                        candidates.append((hwnd, title, pname))
            return True

        win32gui.EnumWindows(enum_cb, None)
        if candidates:
            return candidates[0][0]
    except Exception:
        pass
    return None


def activate_application_window(target_name: str) -> Dict[str, Any]:
    """Bring the existing window of an application to the foreground."""
    clean = target_name.lower().strip()
    hwnd = find_app_window(clean)
    if not hwnd:
        return {"success": False, "found": False, "error": f"No active window found for '{target_name}'."}

    try:
        import win32gui
        import win32con
        import win32process
        import win32api

        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        else:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

        cur_thread = win32api.GetCurrentThreadId()
        target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
        try:
            win32process.AttachThreadInput(cur_thread, target_thread, True)
            win32gui.SetForegroundWindow(hwnd)
            win32process.AttachThreadInput(cur_thread, target_thread, False)
        except Exception:
            win32gui.SetForegroundWindow(hwnd)

        title = win32gui.GetWindowText(hwnd)
        return {
            "success": True,
            "found": True,
            "hwnd": hwnd,
            "title": title,
            "message": f"Activated window '{title or target_name}' and brought to foreground."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to activate window: {str(e)}"}


def set_window_state(target_name: str, state: str) -> Dict[str, Any]:
    """Control window state: 'minimize', 'maximize', 'restore', 'close'."""
    clean = target_name.lower().strip()
    st = state.lower().strip()
    hwnd = find_app_window(clean)
    if not hwnd:
        return {"success": False, "error": f"No active window found for '{target_name}'."}

    try:
        import win32gui
        import win32con
        if st in ["minimize", "min"]:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return {"success": True, "action": "minimize", "message": f"Minimized '{target_name}'."}
        elif st in ["maximize", "max"]:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return {"success": True, "action": "maximize", "message": f"Maximized '{target_name}'."}
        elif st in ["restore", "normal"]:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            return {"success": True, "action": "restore", "message": f"Restored '{target_name}'."}
        elif st in ["close"]:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            return {"success": True, "action": "close", "message": f"Closed '{target_name}' window."}
        else:
            return {"success": False, "error": f"Unknown window state '{state}'. Use minimize, maximize, restore, or close."}
    except Exception as e:
        return {"success": False, "error": f"Failed to set window state: {str(e)}"}


def launch_application(app_id: str, confirmed: bool = False) -> Dict[str, Any]:
    """Launch an allowlisted Windows desktop application with security verification."""
    clean_id = app_id.lower().strip()

    # Check Companion HUD
    if clean_id in ["hud", "companion", "mini_hud", "companion_hud", "floating_hud", "floating_icon"]:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        pythonw = os.path.join(repo_root, ".venv", "Scripts", "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = os.path.join(repo_root, ".venv", "Scripts", "python.exe")
        hud_script = os.path.join(repo_root, "desktop_companion.py")
        subprocess.Popen([pythonw, hud_script], cwd=repo_root)
        return {
            "success": True,
            "app_id": app_id,
            "name": "Floating Companion HUD",
            "message": "Launched J.A.R.V.I.S. Floating Companion HUD on desktop."
        }

    # Check Folder Map (Downloads, Documents, Desktop, Screenshots, etc.)
    if clean_id in FOLDER_MAP:
        folder_path = FOLDER_MAP[clean_id]
        if os.path.exists(folder_path) or folder_path.startswith("shell:"):
            _launch_target(folder_path)
            return {
                "success": True,
                "app_id": app_id,
                "name": clean_id.capitalize(),
                "message": f"Opened {clean_id.capitalize()} folder in Windows Explorer."
            }

    # Check Web Shortcuts
    if clean_id in WEB_SHORTCUTS:
        url = WEB_SHORTCUTS[clean_id]
        webbrowser.open(url)
        return {
            "success": True,
            "app_id": app_id,
            "name": clean_id.capitalize(),
            "message": f"Opened {url} in default browser."
        }

    is_approved = authorizer.is_app_approved(clean_id)

    # If not explicitly in approved config, check if system has it and full_access is enabled
    if not is_approved:
        if authorizer.config.get("full_access_mode", True):
            # Check if already running first
            act_res = activate_application_window(clean_id)
            if act_res.get("success"):
                return {
                    "success": True,
                    "app_id": app_id,
                    "name": act_res.get("title") or clean_id.capitalize(),
                    "already_running": True,
                    "message": f"Application '{clean_id}' is already running. Brought window to the foreground."
                }

            resolved = _find_executable(clean_id)
            if not resolved:
                return {
                    "success": False,
                    "error": f"Application '{app_id}' is not in the authorized desktop allowlist and not found on system path."
                }
            if _launch_target(resolved):
                return {
                    "success": True,
                    "app_id": app_id,
                    "name": os.path.basename(resolved),
                    "message": f"Successfully launched {os.path.basename(resolved)}."
                }
            return {"success": False, "error": f"Failed to launch '{app_id}'."}
        else:
            return {
                "success": False,
                "error": f"Application '{app_id}' is not in the authorized desktop allowlist."
            }

    app_info = authorizer.get_app_info(clean_id) or {}
    if app_info.get("requires_approval") and not confirmed:
        approval_id = authorizer.create_pending_approval("launch_app", {"app_id": app_id})
        return {
            "success": False,
            "requires_confirmation": True,
            "approval_id": approval_id,
            "message": f"Launching '{app_info.get('name', app_id)}' requires explicit confirmation."
        }

    # If application is already running and has an active window, bring it to the foreground!
    act_res = activate_application_window(clean_id)
    if act_res.get("success"):
        return {
            "success": True,
            "app_id": app_id,
            "name": app_info.get("name", app_id),
            "already_running": True,
            "message": f"{app_info.get('name', app_id)} is already running. Brought window to foreground."
        }

    # Check Protocol Map (e.g. WhatsApp, Camera, Calculator, Settings)
    if clean_id in PROTOCOL_MAP:
        proto, web_fallback = PROTOCOL_MAP[clean_id]
        if _launch_target(proto):
            return {
                "success": True,
                "app_id": app_id,
                "name": clean_id.capitalize(),
                "message": f"Successfully launched {clean_id.capitalize()}."
            }
        elif web_fallback:
            webbrowser.open(web_fallback)
            return {
                "success": True,
                "app_id": app_id,
                "name": f"{clean_id.capitalize()} (Web)",
                "message": f"Opened {clean_id.capitalize()} portal in default browser."
            }

    executable = app_info.get("executable", f"{clean_id}.exe")

    # If executable is a protocol scheme (ends with :)
    if executable.endswith(":") or "://" in executable:
        if _launch_target(executable):
            return {
                "success": True,
                "app_id": app_id,
                "name": app_info.get("name", app_id),
                "message": f"Successfully launched {app_info.get('name', app_id)}."
            }

    # Standard executable
    if _launch_target(executable):
        return {
            "success": True,
            "app_id": app_id,
            "name": app_info.get("name", app_id),
            "message": f"Successfully launched {app_info.get('name', app_id)}."
        }

    # Resolve executable via path / start menu
    resolved_exe = _find_executable(executable) or _find_executable(clean_id)
    if resolved_exe and _launch_target(resolved_exe):
        return {
            "success": True,
            "app_id": app_id,
            "name": app_info.get("name", app_id),
            "message": f"Successfully launched {app_info.get('name', app_id)}."
        }

    return {
        "success": False,
        "error": f"Executable '{executable}' could not be executed on this system."
    }


def launch_custom_app(target: str, arguments: Optional[List[str]] = None) -> Dict[str, Any]:
    """Launch ANY application or document by path, shell protocol, or name."""
    clean_target = target.strip()
    if not clean_target:
        return {"success": False, "error": "Target application name or path required."}

    lower = clean_target.lower()

    # If folder
    if lower in FOLDER_MAP:
        folder_path = FOLDER_MAP[lower]
        if os.path.exists(folder_path) or folder_path.startswith("shell:"):
            _launch_target(folder_path)
            return {"success": True, "target": clean_target, "message": f"Opened '{clean_target}' in Explorer."}

    # If in protocol map
    if lower in PROTOCOL_MAP:
        proto, fallback = PROTOCOL_MAP[lower]
        if _launch_target(proto):
            return {"success": True, "target": clean_target, "message": f"Dispatched launch for '{clean_target}'."}
        if fallback:
            webbrowser.open(fallback)
            return {"success": True, "target": clean_target, "message": f"Opened '{clean_target}' in browser."}

    # If web shortcut
    if lower in WEB_SHORTCUTS:
        webbrowser.open(WEB_SHORTCUTS[lower])
        return {"success": True, "target": clean_target, "message": f"Opened '{clean_target}' in browser."}

    # If path exists
    if os.path.exists(clean_target):
        if _launch_target(clean_target):
            return {"success": True, "target": clean_target, "message": f"Successfully opened '{clean_target}'."}

    # Try resolving via Start Menu or Path
    resolved = _find_executable(clean_target)
    if resolved:
        if _launch_target(resolved):
            return {"success": True, "target": resolved, "message": f"Successfully launched '{clean_target}'."}

    # Fallback to direct shell start
    if _launch_target(clean_target):
        return {"success": True, "target": clean_target, "message": f"Dispatched launch directive for '{clean_target}'."}

    return {"success": False, "error": f"Failed to launch '{clean_target}'."}


CHROME_APP_PATHS = [
    os.path.expandvars(r'%ProgramFiles%\Google\Chrome\Application\chrome.exe'),
    os.path.expandvars(r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe'),
    os.path.expandvars(r'%LocalAppData%\Google\Chrome\Application\chrome.exe')
]


def find_chrome_executable() -> Optional[str]:
    w = shutil.which("chrome") or shutil.which("chrome.exe")
    if w:
        return w
    for p in CHROME_APP_PATHS:
        if os.path.isfile(p):
            return p
    return None


def open_browser_url(url: str, browser: Optional[str] = None, confirmed: bool = False) -> Dict[str, Any]:
    """Open a web URL in the specified browser (or system default) after scheme validation."""
    clean_url = url.strip()
    if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
        # Auto-prefix http if domain
        if "." in clean_url and not " " in clean_url:
            clean_url = "https://" + clean_url
        else:
            return {
                "success": False,
                "error": "Security rejection: only http:// and https:// URLs are permitted."
            }

    try:
        if browser and browser.lower() == "chrome":
            chrome_path = find_chrome_executable()
            if chrome_path:
                subprocess.Popen([chrome_path, clean_url])
                return {
                    "success": True,
                    "url": clean_url,
                    "browser": "chrome",
                    "message": f"Opened '{clean_url}' in Google Chrome."
                }

        webbrowser.open(clean_url)
        return {
            "success": True,
            "url": clean_url,
            "message": f"Opened '{clean_url}' in default browser."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to open URL: {str(e)}"
        }
