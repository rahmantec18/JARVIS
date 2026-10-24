import re
from typing import Dict, Any, Optional, Tuple


def parse_tamil_directive(text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Recognize common Tamil conversational directives:
    - 'WhatsApp open pannu'
    - 'Spotify open pannu'
    - 'Believer play pannu'
    - 'Volume koraikkavum' (reduce volume)
    - 'Volume ethavum' (increase volume)
    """
    clean = text.strip().lower()

    # App open pannu
    app_m = re.search(r'^(?:jarvis\s+)?([a-z0-9\s]+?)\s+(?:open|launch|start)\s+pannu(?:\s+pa)?$', clean)
    if app_m:
        app_name = app_m.group(1).strip()
        return "open_app", {"app": app_name}

    # Play pannu
    play_m = re.search(r'^(?:jarvis\s+)?(?:song\s+)?(.+?)\s+(?:song\s+)?play\s+pannu(?:\s+pa)?$', clean)
    if play_m:
        song = play_m.group(1).strip()
        return "play_spotify", {"query": song}

    # Volume controls in Tamil
    if any(k in clean for k in ["volume koraikkavum", "volume kora", "satham kora"]):
        return "control_volume", {"action": "down"}
    if any(k in clean for k in ["volume ethavum", "volume etha", "satham etha"]):
        return "control_volume", {"action": "up"}

    return None


def parse_spotify_directive(text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Parse natural music directives for Spotify:
    - 'Open Spotify and play some song'
    - 'Play Believer by Imagine Dragons'
    - 'Play Arabic Kuthu on Spotify'
    - 'Play my workout playlist'
    - 'Search Spotify for Tamil love songs'
    - 'Pause the song' / 'Resume' / 'Skip' / 'Previous track'
    """
    clean = text.strip()
    lower = clean.lower()

    # Avoid YouTube or browser explicit requests
    if "youtube" in lower or "browser" in lower:
        return None

    # Transport controls
    if lower in ["pause", "pause the song", "pause playback", "pause spotify", "pause music", "stop music", "halt playback"]:
        return "pause_spotify", {}

    if lower in ["resume", "resume the song", "resume playback", "resume spotify", "resume music", "continue playing"]:
        return "resume_spotify", {}

    if lower in ["skip", "skip this song", "skip song", "skip track", "next track", "next song", "play next song"]:
        return "skip_spotify", {}

    if lower in ["previous track", "play previous track", "previous song", "prev track", "rewind", "back track"]:
        return "previous_spotify", {}

    # Play song/playlist
    # Match "open spotify and play X", "open spotify, play X", "play X on spotify", "play X"
    play_match = re.search(
        r'^(?:jarvis\s*,?\s*)?(?:(?:open|launch)\s+spotify\s*(?:and\s+|,|\s+then\s+)?|spotify\s*,?\s*)?(?:play|listen\s+to|stream|put\s+on|start\s+playing|search\s+spotify\s+for)\s*(.*?)(?:\s+on\s+spotify|\s+in\s+spotify)?$',
        clean,
        re.IGNORECASE
    )
    if play_match:
        query = play_match.group(1).strip()
        # If this is a compound directive asking a doubt/explanation, defer to Gemini LLM
        if any(w in query.lower() for w in [" and explain", " and tell", " and what", " and why", " and how", " and summarize", " and clarify", " and describe"]):
            return None
        if not query:
            query = "some song"
        is_playlist = "playlist" in query.lower()
        return "play_spotify", {"query": query, "playlist": is_playlist}

    return None


def parse_youtube_directive(text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Parse natural video / music directives for YouTube:
    - 'Open YouTube and play despacito song'
    - 'Open YouTube and play some music'
    - 'Play Believer on YouTube'
    - 'Search for funny cats on YouTube'
    - 'Watch interstellar trailer on YouTube'
    """
    clean = text.strip()
    lower = clean.lower()

    if "youtube" not in lower:
        return None

    m = re.search(
        r'^(?:jarvis\s*,?\s*)?(?:(?:open|launch)\s+youtube\s*(?:and\s+|,|\s+then\s+)?|youtube\s*,?\s*)?(?:play|search(?:\s+for)?|watch|listen\s+to|stream|put\s+on)\s*(.*?)(?:\s+on\s+youtube|\s+in\s+youtube)?$',
        clean,
        re.IGNORECASE
    )
    if m:
        query = m.group(1).strip().strip('"\'')
        if any(w in query.lower() for w in [" and explain", " and tell", " and what", " and why", " and how", " and summarize", " and clarify", " and describe"]):
            return None
        if not query or query.lower() == "youtube":
            query = "trending music"
        return "play_youtube", {"query": query}

    m2 = re.search(r'^(?:jarvis\s*,?\s*)?open\s+youtube\s+to\s+(?:play|watch|search\s+for)\s+(.+)$', clean, re.IGNORECASE)
    if m2:
        return "play_youtube", {"query": m2.group(1).strip().strip('"\'')}

    return None


def parse_volume_directive(text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Parse master audio volume requests:
    - 'Turn the volume down to 30 percent'
    - 'Set volume to 50%'
    - 'Turn volume up' / 'Volume down'
    - 'Mute audio' / 'Unmute'
    """
    clean = text.strip()
    lower = clean.lower()

    # Exact percentage
    pct_m = re.search(r'(?:turn\s+(?:the\s+)?volume\s+(?:down\s+|up\s+)?to|set\s+(?:the\s+)?volume\s+to|volume\s+to|volume\s+at)\s+(\d{1,3})\s*(?:%|percent)?', clean, re.IGNORECASE)
    if pct_m:
        level = int(pct_m.group(1))
        return "control_volume", {"action": "set", "level": max(0, min(100, level))}

    direct_pct = re.search(r'^volume\s+(\d{1,3})\s*(?:%|percent)?$', lower)
    if direct_pct:
        level = int(direct_pct.group(1))
        return "control_volume", {"action": "set", "level": max(0, min(100, level))}

    # Relative volume
    if any(w in lower for w in ["volume up", "increase volume", "louder", "turn it up", "turn the volume up"]):
        return "control_volume", {"action": "up"}

    if any(w in lower for w in ["volume down", "decrease volume", "quieter", "lower volume", "turn it down", "turn the volume down"]):
        return "control_volume", {"action": "down"}

    if any(w in lower for w in ["mute audio", "mute sound", "mute volume", "mute"]):
        return "control_volume", {"action": "mute"}

    if any(w in lower for w in ["unmute audio", "unmute sound", "unmute volume", "unmute"]):
        return "control_volume", {"action": "unmute"}

    return None


def parse_window_state_directive(text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Parse window minimize, maximize, restore, or close commands:
    - 'Minimize the window'
    - 'Minimize Spotify'
    - 'Maximize Chrome'
    """
    clean = text.strip()
    lower = clean.lower()

    m = re.search(r'^(?:jarvis\s*,?\s*)?(minimize|maximize|restore|close)(?:\s+the\s+window|\s+window|\s+the\s+app)?(?:\s+(?:of\s+|for\s+)?(.+))?$', lower)
    if m:
        action = m.group(1)
        target = (m.group(2) or "").strip()
        return "set_window_state", {"target": target, "state": action}

    return None
