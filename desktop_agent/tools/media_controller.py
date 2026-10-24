import ctypes
import subprocess
from typing import Dict, Any, Optional, List

# Windows Virtual Key Codes for Hardware Media Controls
VK_VOLUME_MUTE = 0xAD       # 173
VK_VOLUME_DOWN = 0xAE       # 174
VK_VOLUME_UP = 0xAF         # 175
VK_MEDIA_NEXT_TRACK = 0xB0   # 176
VK_MEDIA_PREV_TRACK = 0xB1   # 177
VK_MEDIA_STOP = 0xB2         # 178
VK_MEDIA_PLAY_PAUSE = 0xB3    # 179

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002


def _send_vk(vk_code: int):
    """Dispatch a hardware key press and release event."""
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
        user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
        return True
    except Exception:
        return False


def _get_pycaw_volume():
    """Obtain the master audio endpoint volume interface via pycaw."""
    try:
        from pycaw.pycaw import AudioUtilities
        device = AudioUtilities.GetSpeakers()
        return device.EndpointVolume
    except Exception:
        return None


def control_volume(action: str, level: Optional[int] = None) -> Dict[str, Any]:
    """
    Control Windows system audio volume with exact percentage precision or relative increments.
    Actions: 'set', 'up', 'down', 'mute', 'unmute', 'toggle_mute', 'get'.
    """
    act = (action or "").lower().strip()
    vol_endpoint = _get_pycaw_volume()

    try:
        # Check if direct numeric level is passed in action (e.g. "30" or "30%")
        if level is None and (act.isdigit() or (act.endswith("%") and act[:-1].isdigit())):
            level = int(act.replace("%", ""))
            act = "set"

        if act == "set" or level is not None:
            if level is None:
                return {"success": False, "error": "Volume level (0-100) must be specified for 'set' action."}
            target_level = max(0, min(100, int(level)))
            scalar = target_level / 100.0

            if vol_endpoint:
                vol_endpoint.SetMasterVolumeLevelScalar(scalar, None)
                vol_endpoint.SetMute(0, None)  # Ensure unmuted
                return {
                    "success": True,
                    "action": "set",
                    "level": target_level,
                    "message": f"Master volume calibrated to {target_level} percent."
                }
            else:
                # Fallback to PowerShell
                ps_script = f"$w = New-Object -ComObject WScript.Shell; 1..50 | ForEach-Object {{ $w.SendKeys([char]174) }}; 1..{target_level // 2} | ForEach-Object {{ $w.SendKeys([char]175) }}"
                subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_script], capture_output=True, timeout=5)
                return {
                    "success": True,
                    "action": "set",
                    "level": target_level,
                    "message": f"Master volume set to approximately {target_level}%."
                }

        elif act in ["up", "increase", "louder"]:
            step = 10
            if vol_endpoint:
                current_scalar = vol_endpoint.GetMasterVolumeLevelScalar()
                new_scalar = min(1.0, current_scalar + (step / 100.0))
                vol_endpoint.SetMasterVolumeLevelScalar(new_scalar, None)
                vol_endpoint.SetMute(0, None)
                final_pct = int(round(new_scalar * 100))
                return {
                    "success": True,
                    "action": "up",
                    "level": final_pct,
                    "message": f"Master volume elevated to {final_pct}%."
                }
            else:
                _send_vk(VK_VOLUME_UP)
                _send_vk(VK_VOLUME_UP)
                _send_vk(VK_VOLUME_UP)
                return {"success": True, "action": "up", "message": "Master volume increased."}

        elif act in ["down", "decrease", "lower", "quieter"]:
            step = 10
            if vol_endpoint:
                current_scalar = vol_endpoint.GetMasterVolumeLevelScalar()
                new_scalar = max(0.0, current_scalar - (step / 100.0))
                vol_endpoint.SetMasterVolumeLevelScalar(new_scalar, None)
                final_pct = int(round(new_scalar * 100))
                return {
                    "success": True,
                    "action": "down",
                    "level": final_pct,
                    "message": f"Master volume attenuated to {final_pct}%."
                }
            else:
                _send_vk(VK_VOLUME_DOWN)
                _send_vk(VK_VOLUME_DOWN)
                _send_vk(VK_VOLUME_DOWN)
                return {"success": True, "action": "down", "message": "Master volume decreased."}

        elif act == "mute":
            if vol_endpoint:
                vol_endpoint.SetMute(1, None)
            else:
                _send_vk(VK_VOLUME_MUTE)
            return {"success": True, "action": "mute", "message": "Master acoustic channels muted."}

        elif act == "unmute":
            if vol_endpoint:
                vol_endpoint.SetMute(0, None)
            else:
                _send_vk(VK_VOLUME_MUTE)
            return {"success": True, "action": "unmute", "message": "Audio channels restored to nominal output."}

        elif act in ["toggle_mute", "mute_toggle"]:
            if vol_endpoint:
                is_muted = bool(vol_endpoint.GetMute())
                vol_endpoint.SetMute(not is_muted, None)
                state = "muted" if not is_muted else "unmuted"
                return {"success": True, "action": state, "message": f"Master audio {state}."}
            else:
                _send_vk(VK_VOLUME_MUTE)
                return {"success": True, "action": "toggle_mute", "message": "Audio mute toggled."}

        elif act in ["get", "status", "query"]:
            if vol_endpoint:
                pct = int(round(vol_endpoint.GetMasterVolumeLevelScalar() * 100))
                muted = bool(vol_endpoint.GetMute())
                return {"success": True, "level": pct, "muted": muted, "message": f"Volume is at {pct}% ({'muted' if muted else 'active'})."}
            return {"success": True, "level": 50, "muted": False, "message": "Volume is operational."}

        else:
            return {"success": False, "error": f"Unsupported volume directive '{action}'. Use set, up, down, mute, or unmute."}

    except Exception as e:
        return {"success": False, "error": f"Volume control failure: {str(e)}"}


def control_media(action: str) -> Dict[str, Any]:
    """
    Control Windows system media playback using hardware virtual keys.
    Supported actions: 'play', 'pause', 'play_pause', 'next', 'skip', 'previous', 'prev', 'stop'.
    """
    act = (action or "").lower().strip()
    try:
        if act in ["play", "pause", "play_pause", "toggle", "resume"]:
            _send_vk(VK_MEDIA_PLAY_PAUSE)
            return {
                "success": True,
                "action": "play_pause",
                "message": "Dispatched Play/Pause media transport directive."
            }

        elif act in ["next", "skip", "next_track"]:
            _send_vk(VK_MEDIA_NEXT_TRACK)
            return {
                "success": True,
                "action": "next",
                "message": "Skipped to next media track."
            }

        elif act in ["prev", "previous", "previous_track", "back"]:
            _send_vk(VK_MEDIA_PREV_TRACK)
            return {
                "success": True,
                "action": "previous",
                "message": "Rewound to previous media track."
            }

        elif act in ["stop"]:
            _send_vk(VK_MEDIA_STOP)
            return {
                "success": True,
                "action": "stop",
                "message": "Media playback halted."
            }

        else:
            return {
                "success": False,
                "error": f"Unsupported media directive '{action}'. Valid: play, pause, next, previous, stop."
            }

    except Exception as e:
        return {"success": False, "error": f"Media control error: {str(e)}"}


def check_active_audio_sessions(target_process_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Query Windows CoreAudio API via pycaw to detect which applications are producing audio.
    Returns session states and peak audio meters to verify active sound generation.
    """
    try:
        from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
        sessions = AudioUtilities.GetAllSessions()
        active = []
        target_found = False
        target_playing = False
        target_peak = 0.0

        for session in sessions:
            p = session.Process
            name = p.name() if p else "System"
            state = getattr(session, "State", 0)
            peak = 0.0
            try:
                if hasattr(session, "_ctl") and session._ctl:
                    meter = session._ctl.QueryInterface(IAudioMeterInformation)
                    peak = float(meter.GetPeakValue())
            except Exception:
                peak = 0.0

            is_active = (state == 1) or (peak > 0.001)
            session_info = {"process": name, "peak": round(peak, 4), "state": state, "is_active": is_active}
            active.append(session_info)

            if target_process_name and target_process_name.lower() in name.lower():
                target_found = True
                if is_active:
                    target_playing = True
                if peak > target_peak:
                    target_peak = peak

        return {
            "success": True,
            "sessions": active,
            "target_found": target_found,
            "target_peak": target_peak,
            "target_playing": target_playing
        }
    except Exception as e:
        return {"success": False, "error": str(e), "sessions": [], "target_found": False, "target_playing": False}


def lock_workstation() -> Dict[str, Any]:
    """Lock the Windows desktop session."""
    try:
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], shell=False, timeout=5)
        return {"success": True, "message": "Windows workstation locked successfully."}
    except Exception as e:
        return {"success": False, "error": f"Failed to lock workstation: {str(e)}"}


def open_windows_settings(page: str = "") -> Dict[str, Any]:
    """Open Windows modern Settings app, optionally to a specific subpage."""
    clean_page = page.strip().lower()
    # Map common aliases
    PAGE_MAP = {
        "bluetooth": "bluetooth",
        "wifi": "network-wifi",
        "network": "network",
        "sound": "sound",
        "audio": "sound",
        "display": "display",
        "battery": "batterysaver",
        "power": "powersleep",
        "apps": "appsfeatures",
        "updates": "windowsupdate",
        "update": "windowsupdate",
    }
    actual_page = PAGE_MAP.get(clean_page, clean_page)
    uri = f"ms-settings:{actual_page}" if actual_page else "ms-settings:"
    try:
        subprocess.Popen(["cmd.exe", "/c", "start", uri], shell=False)
        return {"success": True, "uri": uri, "message": f"Opened Windows Settings ({uri})."}
    except Exception as e:
        return {"success": False, "error": f"Failed to open settings: {str(e)}"}
