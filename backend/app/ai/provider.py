import re
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Optional
from openai import AsyncOpenAI
from app.core.config import settings
from app.models.schemas import ToolCallDetail, ChatResponse
from app.tools.registry import tool_registry
from app.assistant.planner import MultiStepPlanner
from app.assistant.intent_router import (
    parse_tamil_directive,
    parse_spotify_directive,
    parse_youtube_directive,
    parse_volume_directive,
    parse_window_state_directive
)

logger = logging.getLogger("jarvis.ai")


class BaseAIProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        memories: List[str] = None,
        stream: bool = False
    ) -> ChatResponse:
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        memories: List[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        pass


async def check_fast_path_action(user_message: str, preferred_browser: Optional[str] = None) -> Optional[ChatResponse]:
    """
    Zero-Latency Fast-Path Reflex Router.
    Executes immediate desktop actions, app launches, volume, system status,
    and media operations in < 15ms without external LLM network latency.
    """
    if not user_message:
        return None

    clean = user_message.strip()
    lower = clean.lower()
    executed_tools: List[ToolCallDetail] = []

    # Spotify Music Playback & Transport Controls (Prioritized for zero-latency direct obedience)
    spotify_parsed = parse_spotify_directive(clean)
    if spotify_parsed:
        act_name, args = spotify_parsed
        if act_name == "play_spotify":
            res = await tool_registry.execute("play_spotify_music", args)
            executed_tools.append(ToolCallDetail(
                id="call_spotify_play",
                name="play_spotify_music",
                arguments=args,
                result=res.result or {},
                status="success" if (res.success and res.result and res.result.get("success")) else "failed"
            ))
            track_msg = str((res.result.get("message") if res.result else None) or (res.result.get("error") if res.result else None) or "Playback initiated on Spotify, sir.")
            return ChatResponse(
                conversation_id="",
                message=track_msg,
                tool_calls=executed_tools,
                status="success" if (res.success and res.result and res.result.get("success")) else "error"
            )
        elif act_name == "pause_spotify":
            res = await tool_registry.execute("pause_spotify_music", {})
            return ChatResponse(
                conversation_id="",
                message="Spotify playback paused, sir.",
                tool_calls=[ToolCallDetail(id="call_spot_pause", name="pause_spotify_music", arguments={}, result=res.result, status="success")],
                status="success"
            )
        elif act_name == "resume_spotify":
            res = await tool_registry.execute("resume_spotify_music", {})
            return ChatResponse(
                conversation_id="",
                message="Spotify playback resumed, sir.",
                tool_calls=[ToolCallDetail(id="call_spot_resume", name="resume_spotify_music", arguments={}, result=res.result, status="success")],
                status="success"
            )
        elif act_name == "skip_spotify":
            res = await tool_registry.execute("skip_spotify_track", {})
            return ChatResponse(
                conversation_id="",
                message="Skipped to next track on Spotify, sir.",
                tool_calls=[ToolCallDetail(id="call_spot_skip", name="skip_spotify_track", arguments={}, result=res.result, status="success")],
                status="success"
            )
        elif act_name == "previous_spotify":
            res = await tool_registry.execute("previous_spotify_track", {})
            return ChatResponse(
                conversation_id="",
                message="Returned to previous track on Spotify, sir.",
                tool_calls=[ToolCallDetail(id="call_spot_prev", name="previous_spotify_track", arguments={}, result=res.result, status="success")],
                status="success"
            )

    # YouTube Video / Music Playback Directives
    yt_parsed = parse_youtube_directive(clean)
    if yt_parsed:
        _, args = yt_parsed
        query = args.get("query", "").strip()
        import urllib.parse
        yt_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        browser_to_use = preferred_browser or ("chrome" if "chrome" in lower else None)
        w_args = {"url": yt_url, "browser": browser_to_use} if browser_to_use else {"url": yt_url}
        res = await tool_registry.execute("open_website", w_args)
        executed_tools.append(ToolCallDetail(
            id="call_yt",
            name="open_website",
            arguments=w_args,
            result=res.result or {},
            status="success" if res.success else "failed"
        ))
        return ChatResponse(
            conversation_id="",
            message=f"Playing *\"{query}\"* on YouTube, sir.",
            tool_calls=executed_tools,
            status="success"
        )

    # Fast check for Compound Chrome + Destination directive
    # "open chrome and open youtube", "open chrome and search for youtube", "open chrome and go to youtube"
    chrome_combo = re.search(
        r'^(?:open|launch)\s+(?:google\s+)?chrome\s+and\s+(?:open|launch|go\s+to|navigate(?:\s+to)?|search(?:\s+for)?|visit)\s+["\']?(.+?)["\']?$',
        clean,
        re.IGNORECASE
    )
    if chrome_combo:
        raw_target = chrome_combo.group(1).strip()
        lower_target = raw_target.lower()
        chrome_web_map = {
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "gmail": "https://mail.google.com",
            "github": "https://www.github.com",
            "chatgpt": "https://chatgpt.com",
            "twitter": "https://twitter.com",
            "x": "https://x.com",
            "reddit": "https://reddit.com",
            "netflix": "https://www.netflix.com",
            "amazon": "https://www.amazon.com"
        }
        if lower_target in chrome_web_map:
            dest_url = chrome_web_map[lower_target]
            site_label = lower_target.capitalize()
        elif lower_target.startswith("http://") or lower_target.startswith("https://"):
            dest_url = lower_target
            site_label = raw_target
        elif "." in lower_target and " " not in lower_target:
            dest_url = f"https://{lower_target}"
            site_label = raw_target
        else:
            import urllib.parse
            dest_url = f"https://www.google.com/search?q={urllib.parse.quote(raw_target)}"
            site_label = f"search for '{raw_target}'"

        c_res = await tool_registry.execute("open_approved_app", {"app_id": "chrome"})
        executed_tools.append(ToolCallDetail(id="call_open_chrome", name="open_approved_app", arguments={"app_id": "chrome"}, result=c_res.result or {}, status="success"))
        w_res = await tool_registry.execute("open_website", {"url": dest_url, "browser": "chrome"})
        executed_tools.append(ToolCallDetail(id="call_open_web", name="open_website", arguments={"url": dest_url, "browser": "chrome"}, result=w_res.result or {}, status="success"))
        return ChatResponse(
            conversation_id="",
            message=f"Opening Google Chrome and loading {site_label}, sir.",
            tool_calls=executed_tools,
            status="success"
        )

    # Compound / Multi-Step Directives
    if MultiStepPlanner.is_compound_directive(clean):
        steps = MultiStepPlanner.parse_plan(clean)
        return await MultiStepPlanner.execute_plan(steps)

    # Tamil conversational directives
    tamil_parsed = parse_tamil_directive(clean)
    if tamil_parsed:
        action_type, args = tamil_parsed
        if action_type == "open_app":
            app_target = args.get("app", "")
            res = await tool_registry.execute("open_approved_app", {"app_id": app_target})
            return ChatResponse(
                conversation_id="",
                message=f"Opening {app_target.capitalize()} for you, sir.",
                tool_calls=[ToolCallDetail(id="call_tamil_app", name="open_approved_app", arguments={"app_id": app_target}, result=res.result, status="success")],
                status="success"
            )
        elif action_type == "play_spotify":
            res = await tool_registry.execute("play_spotify_music", {"query": args.get("query", "")})
            msg = res.result.get("message", "Playing on Spotify, sir.") if res.result else "Dispatched playback on Spotify, sir."
            return ChatResponse(
                conversation_id="",
                message=msg,
                tool_calls=[ToolCallDetail(id="call_tamil_spot", name="play_spotify_music", arguments=args, result=res.result, status="success")],
                status="success"
            )
        elif action_type == "control_volume":
            res = await tool_registry.execute("control_system_volume", args)
            return ChatResponse(
                conversation_id="",
                message=res.result.get("message", "Volume adjusted, sir.") if res.result else "Volume adjusted, sir.",
                tool_calls=[ToolCallDetail(id="call_tamil_vol", name="control_system_volume", arguments=args, result=res.result, status="success")],
                status="success"
            )

    # Master Volume Controls (Exact percentage or relative)
    vol_parsed = parse_volume_directive(clean)
    if vol_parsed:
        _, args = vol_parsed
        res = await tool_registry.execute("control_system_volume", args)
        executed_tools.append(ToolCallDetail(
            id="call_vol_ctrl",
            name="control_system_volume",
            arguments=args,
            result=res.result or {},
            status="success"
        ))
        vol_msg = str((res.result.get("message") if res.result else None) or (res.result.get("error") if res.result else None) or "Master audio adjusted, sir.")
        return ChatResponse(
            conversation_id="",
            message=f"{vol_msg}, sir." if not vol_msg.endswith("sir.") else vol_msg,
            tool_calls=executed_tools,
            status="success"
        )

    # Window State Controls (Minimize, Maximize, Restore, Close)
    win_parsed = parse_window_state_directive(clean)
    if win_parsed:
        _, args = win_parsed
        res = await tool_registry.execute("set_desktop_window_state", args)
        executed_tools.append(ToolCallDetail(
            id="call_win_state",
            name="set_desktop_window_state",
            arguments=args,
            result=res.result or {},
            status="success"
        ))
        msg = str((res.result.get("message") if res.result else None) or (res.result.get("error") if res.result else None) or "Window state adjusted, sir.")
        return ChatResponse(
            conversation_id="",
            message=f"{msg}, sir." if not msg.endswith("sir.") else msg,
            tool_calls=executed_tools,
            status="success"
        )

    # 0. DELETION & REMOVAL DIRECTIVES (< 15ms)
    # "delete test.txt", "delete file note.md", "delete screenshot", "delete screenshots", "delete folder temp", "empty recycle bin"
    del_match = re.search(r'^(?:delete|remove|erase|clear|clean|empty)\s+(?:the\s+)?(?:file\s+|folder\s+|directory\s+)?(.+?)$', clean, re.IGNORECASE)
    if del_match:
        target_item = del_match.group(1).strip().strip('"\'')
        res = await tool_registry.execute("delete_system_item", {"target": target_item})
        executed_tools.append(ToolCallDetail(
            id="call_delete",
            name="delete_system_item",
            arguments={"target": target_item},
            result=res.result or {"error": res.error},
            status="success" if (res.success and res.result and res.result.get("success")) else "failed"
        ))
        msg = res.result.get("message", res.error or "Deletion completed.") if res.result else (res.error or "Target could not be located.")
        return ChatResponse(
            conversation_id="",
            message=f"{msg}, sir." if not msg.endswith("sir.") else msg,
            tool_calls=executed_tools,
            status="success" if (res.success and res.result and res.result.get("success")) else "error"
        )

    # 00A. FOLDER CREATION DIRECTIVES (< 15ms)
    # "Create a folder named College Projects in Documents"
    folder_create_m = re.search(r'^(?:create|make)\s+(?:a\s+)?folder\s+(?:named\s+|called\s+)?["\']?([^"\']+)["\']?(?:\s+in\s+([a-zA-Z]+))?$', clean, re.IGNORECASE)
    if folder_create_m:
        f_name = folder_create_m.group(1).strip()
        f_parent = (folder_create_m.group(2) or "documents").strip().lower()
        res = await tool_registry.execute("create_desktop_directory", {"folder_name": f_name, "parent_folder": f_parent})
        executed_tools.append(ToolCallDetail(
            id="call_create_dir",
            name="create_desktop_directory",
            arguments={"folder_name": f_name, "parent_folder": f_parent},
            result=res.result or {},
            status="success" if (res.success and res.result and res.result.get("success")) else "failed"
        ))
        msg = str((res.result.get("message") if res.result else None) or (res.result.get("error") if res.result else None) or f"Folder '{f_name}' created.")
        return ChatResponse(
            conversation_id="",
            message=f"{msg}, sir." if not msg.endswith("sir.") else msg,
            tool_calls=executed_tools,
            status="success" if (res.success and res.result and res.result.get("success")) else "error"
        )

    # 00B. KNOWN FOLDER NAVIGATION
    nav_folder_m = re.search(r'^(?:go\s+to|open|show|explore)\s+(?:the\s+)?(downloads|documents|desktop|pictures|music|videos|screenshots|notes)(?:\s+folder)?$', clean, re.IGNORECASE)
    if nav_folder_m:
        f_target = nav_folder_m.group(1).strip().lower()
        res = await tool_registry.execute("open_approved_app", {"app_id": f_target})
        return ChatResponse(
            conversation_id="",
            message=f"Opening your {f_target.capitalize()} folder in Windows Explorer, sir.",
            tool_calls=[ToolCallDetail(id="call_open_folder", name="open_approved_app", arguments={"app_id": f_target}, result=res.result, status="success")],
            status="success"
        )

    # 00C. ADVANCED FILE SEARCH & OPEN
    if any(w in lower for w in ["latest screenshot and open", "last screenshot and open", "open latest screenshot"]):
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        sc_dir = repo_root / "screenshots"
        pngs = sorted(sc_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
        if pngs:
            top_sc = str(pngs[0])
            res = await tool_registry.execute("launch_custom_application", {"target": top_sc})
            return ChatResponse(
                conversation_id="",
                message=f"Opening your latest screenshot `{pngs[0].name}`, sir.",
                tool_calls=[ToolCallDetail(id="call_open_sc", name="launch_custom_application", arguments={"target": top_sc}, result=res.result, status="success")],
                status="success"
            )

    file_search_m = re.search(r'^(?:find|search(?:\s+for)?)\s+(.+?)(?:\s+in\s+([a-zA-Z]+))?$', clean, re.IGNORECASE)
    if file_search_m and any(kw in lower for kw in ["file", "pdf", "report", "resume", "project", ".py", "screenshot", "document", "larger than", "mb"]):
        raw_target = file_search_m.group(1).strip()
        folder_scope = (file_search_m.group(2) or "project").strip().lower()
        auto_open = "and open" in raw_target.lower()
        clean_target = re.sub(r'\s+and\s+open(?:\s+it)?$', '', raw_target, flags=re.IGNORECASE).strip()

        ext = None
        if "pdf" in clean_target.lower():
            ext = ".pdf"
            clean_target = re.sub(r'\bpdf\b', '', clean_target, flags=re.IGNORECASE).strip()
        elif "python" in clean_target.lower() or ".py" in clean_target.lower():
            ext = ".py"
            clean_target = re.sub(r'\bpython\s+files?\b|\.py', '', clean_target, flags=re.IGNORECASE).strip()

        clean_target = re.sub(r'^(?:every|all|my|a)\s+', '', clean_target, flags=re.IGNORECASE)
        clean_target = re.sub(r'containing\s+', '', clean_target, flags=re.IGNORECASE)
        clean_target = re.sub(r'in\s+its\s+filename', '', clean_target, flags=re.IGNORECASE).strip()

        min_mb = None
        size_m = re.search(r'larger\s+than\s+(\d+)\s*mb', clean, re.IGNORECASE)
        if size_m:
            min_mb = float(size_m.group(1))
            clean_target = ""

        from desktop_agent.tools.file_manager import search_files
        search_res = search_files(query=clean_target, base_dir=folder_scope, extension=ext, min_size_mb=min_mb, max_results=10)
        files = search_res.get("files", [])
        executed_tools.append(ToolCallDetail(
            id="call_find_files",
            name="search_files",
            arguments={"query": clean_target, "base_dir": folder_scope, "extension": ext, "min_size_mb": min_mb},
            result=search_res,
            status="success"
        ))

        if not files:
            return ChatResponse(
                conversation_id="",
                message=f"I searched {folder_scope.capitalize()} but found no matching files for *\"{raw_target}\"*, sir.",
                tool_calls=executed_tools,
                status="success"
            )

        if auto_open and files:
            top_file = files[0]["path"]
            open_res = await tool_registry.execute("launch_custom_application", {"target": top_file})
            executed_tools.append(ToolCallDetail(
                id="call_auto_open",
                name="launch_custom_application",
                arguments={"target": top_file},
                result=open_res.result,
                status="success"
            ))
            return ChatResponse(
                conversation_id="",
                message=f"Located and opened `{files[0]['name']}` ({files[0]['size_kb']} KB), sir.\n\nPath: `{top_file}`",
                tool_calls=executed_tools,
                status="success"
            )

        file_list_str = "\n".join([f"- **{f['name']}** ({f['size_kb']} KB) — `{f['path']}`" for f in files[:5]])
        return ChatResponse(
            conversation_id="",
            message=f"Found {len(files)} matching file(s) in {folder_scope.capitalize()}, sir:\n\n{file_list_str}",
            tool_calls=executed_tools,
            status="success"
        )

    # 0A. YOUTUBE DIRECTIVES
    # "play lofi on youtube", "search youtube for news"
    yt_match = re.search(r'^(?:play|search)\s+(.+?)\s+on\s+youtube$', clean, re.IGNORECASE)
    if yt_match:
        query = yt_match.group(1).strip()
        import urllib.parse
        yt_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        res = await tool_registry.execute("open_website", {"url": yt_url})
        return ChatResponse(
            conversation_id="",
            message=f"Playing *\"{query}\"* on YouTube, sir.",
            tool_calls=[ToolCallDetail(id="call_yt", name="open_website", arguments={"url": yt_url}, result=res.result, status="success")],
            status="success"
        )

    # 0B. GENERAL GOOGLE SEARCH DIRECTIVES
    # "search for best laptops", "google weather today", "search for youtube"
    search_match = re.search(r'^(?:search\s+for|search|google)\s+(.+?)(?:\s+on\s+google|\s+in\s+chrome)?$', clean, re.IGNORECASE)
    if search_match and not any(w in lower for w in ["file", "files"]):
        query = search_match.group(1).strip()
        lower_q = query.lower()
        browser_to_use = preferred_browser or ("chrome" if "chrome" in lower else None)
        quick_web = {"youtube": "https://www.youtube.com", "google": "https://www.google.com", "github": "https://www.github.com", "chatgpt": "https://chatgpt.com"}
        if lower_q in quick_web:
            dest_url = quick_web[lower_q]
            w_args = {"url": dest_url, "browser": browser_to_use} if browser_to_use else {"url": dest_url}
            res = await tool_registry.execute("open_website", w_args)
            b_desc = "Google Chrome" if browser_to_use == "chrome" else "browser"
            return ChatResponse(
                conversation_id="",
                message=f"Opening {lower_q.capitalize()} in {b_desc}, sir.",
                tool_calls=[ToolCallDetail(id="call_web_direct", name="open_website", arguments=w_args, result=res.result, status="success")],
                status="success"
            )
        else:
            import urllib.parse
            g_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            w_args = {"url": g_url, "browser": browser_to_use} if browser_to_use else {"url": g_url}
            res = await tool_registry.execute("open_website", w_args)
            return ChatResponse(
                conversation_id="",
                message=f"Executing search directive for *\"{query}\"*, sir.",
                tool_calls=[ToolCallDetail(id="call_search", name="open_website", arguments=w_args, result=res.result, status="success")],
                status="success"
            )

    # 0C. WHATSAPP DIRECT MESSAGING AUTOMATION (< 15ms)
    # "send hi message to Motu", "send hi to Shalini", "text Motu where are you", "send a message to Motu saying hi"
    clean_wa = re.sub(r'\s+on\s+whatsapp$', '', clean, flags=re.IGNORECASE).strip()
    wa_c = None
    wa_m = None

    # Case A: 'send a message to Motu saying/with hi'
    mA = re.search(r'^(?:open\s+whatsapp\s+and\s+)?(?:send|text|message)\s+(?:a\s+)?(?:message\s+)?to\s+[\'"]?(.+?)[\'"]?\s+(?:saying|that|with|texting)\s+[\'"]?(.+?)[\'"]?$', clean_wa, re.IGNORECASE)
    if mA:
        wa_c, wa_m = mA.group(1).strip(), mA.group(2).strip()
    else:
        # Case B: 'send [msg] to [contact]' or 'send hi message to [contact]'
        mB = re.search(r'^(?:open\s+whatsapp\s+and\s+)?(?:send|text|message)\s+[\'"]?(.+?)[\'"]?\s+to\s+[\'"]?(.+?)[\'"]?$', clean_wa, re.IGNORECASE)
        if mB:
            raw_msg, wa_c = mB.group(1).strip(), mB.group(2).strip()
            msg_clean = re.sub(r'^(?:a\s+)?message\s+(?:saying\s+)?', '', raw_msg, flags=re.IGNORECASE)
            msg_clean = re.sub(r'\s+message$', '', msg_clean, flags=re.IGNORECASE)
            wa_m = msg_clean.strip() or "Hi"
        else:
            # Case C: 'text/message [contact] [msg]' or 'send [contact] [msg]'
            mC = re.search(r'^(?:open\s+whatsapp\s+and\s+)?(?:send|text|message|tell)\s+[\'"]?([^\'"]+?)[\'"]?\s+(?:saying|that|with)?\s*[\'"]?(.+?)[\'"]?$', clean_wa, re.IGNORECASE)
            if mC and any(w in lower for w in ["whatsapp", "text ", "message ", "send "]):
                wa_c, wa_m = mC.group(1).strip(), mC.group(2).strip()

    if wa_c and wa_m:
        res = await tool_registry.execute("send_whatsapp_message", {"contact": wa_c, "message": wa_m})
        executed_tools.append(ToolCallDetail(
            id="call_wa_msg",
            name="send_whatsapp_message",
            arguments={"contact": wa_c, "message": wa_m},
            result=res.result or {},
            status="success" if res.success else "failed"
        ))
        return ChatResponse(
            conversation_id="",
            message=f"Directly transmitted WhatsApp message to {wa_c}: *\"{wa_m}\"*, sir.",
            tool_calls=executed_tools,
            status="success"
        )

    # 0B. CHROME SEARCH DIRECTIVES
    # "open chrome and search for youtube", "open google chrome and search for best websites"
    chrome_search = re.search(r'(?:open\s+(?:google\s+)?chrome\s+and\s+)?search\s+(?:for\s+)?["\']?(.+?)["\']?(?:\s+on\s+(?:google\s+)?chrome|\s+in\s+chrome)?$', clean, re.IGNORECASE)
    if chrome_search and any(w in lower for w in ["chrome", "search"]):
        raw_query = chrome_search.group(1).strip()
        if "youtube" in raw_query.lower():
            res = await tool_registry.execute("open_website", {"url": "https://www.youtube.com"})
            return ChatResponse(
                conversation_id="",
                message="Opening YouTube in Google Chrome, sir.",
                tool_calls=[ToolCallDetail(id="call_yt", name="open_website", arguments={"url": "https://www.youtube.com"}, result=res.result, status="success")],
                status="success"
            )
        else:
            import urllib.parse
            encoded = urllib.parse.quote(raw_query)
            search_url = f"https://www.google.com/search?q={encoded}"
            res = await tool_registry.execute("open_website", {"url": search_url})
            return ChatResponse(
                conversation_id="",
                message=f"Opening Google Chrome and executing search directive for *\"{raw_query}\"*, sir.",
                tool_calls=[ToolCallDetail(id="call_search", name="open_website", arguments={"url": search_url}, result=res.result, status="success")],
                status="success"
            )

    # 0D. POP-UP COMPANION HUD DEPLOYMENT
    if any(k in lower for k in ["pop up voice", "popup voice", "float mic", "pop out mic", "pop up the voice", "floating companion", "open hud", "pop up hud", "pop up option"]):
        res = await tool_registry.execute("launch_companion_hud", {})
        executed_tools.append(ToolCallDetail(
            id="call_launch_hud",
            name="launch_companion_hud",
            arguments={},
            result=res.result or {},
            status="success" if res.success else "failed"
        ))
        return ChatResponse(
            conversation_id="",
            message="J.A.R.V.I.S. Floating Companion Voice HUD deployed to your desktop, sir. You can drag it anywhere and speak directives over any application.",
            tool_calls=executed_tools,
            status="success"
        )

    # 1. SCREENSHOT / SCREEN CAPTURE
    if any(w in lower for w in ["screenshot", "capture screen", "take a screen", "take a screenshot", "snap screen"]):
        res = await tool_registry.execute("capture_desktop_screenshot", {})
        executed_tools.append(ToolCallDetail(
            id="call_screenshot",
            name="capture_desktop_screenshot",
            arguments={},
            result=res.result or {"error": res.error},
            status="success" if res.success else "failed"
        ))
        if res.success and res.result.get("success"):
            fname = res.result.get("file_name")
            kb = res.result.get("size_kb")
            return ChatResponse(
                conversation_id="",
                message=f"Visual telemetry acquired, sir. Primary monitor screenshot captured and saved as `{fname}` ({kb} KB).",
                tool_calls=executed_tools,
                status="success",
                suggested_actions=["Open screenshots folder", "Check system status"]
            )
        else:
            return ChatResponse(
                conversation_id="",
                message="Visual telemetry capture executed, sir.",
                tool_calls=executed_tools,
                status="success"
            )

    # 2. VOLUME & AUDIO CONTROLS
    if any(w in lower for w in ["mute audio", "mute sound", "mute volume", "mute"]):
        res = await tool_registry.execute("control_system_volume", {"action": "mute"})
        executed_tools.append(ToolCallDetail(
            id="call_mute",
            name="control_system_volume",
            arguments={"action": "mute"},
            result=res.result or {},
            status="success"
        ))
        return ChatResponse(
            conversation_id="",
            message="Master acoustic channels muted, sir.",
            tool_calls=executed_tools,
            status="success"
        )

    if any(w in lower for w in ["unmute audio", "unmute sound", "unmute volume", "unmute"]):
        res = await tool_registry.execute("control_system_volume", {"action": "unmute"})
        executed_tools.append(ToolCallDetail(
            id="call_unmute",
            name="control_system_volume",
            arguments={"action": "unmute"},
            result=res.result or {},
            status="success"
        ))
        return ChatResponse(
            conversation_id="",
            message="Audio feeds restored to nominal output levels, sir.",
            tool_calls=executed_tools,
            status="success"
        )

    if any(w in lower for w in ["volume up", "increase volume", "louder", "turn it up"]):
        res = await tool_registry.execute("control_system_volume", {"action": "up"})
        executed_tools.append(ToolCallDetail(
            id="call_vol_up",
            name="control_system_volume",
            arguments={"action": "up"},
            result=res.result or {},
            status="success"
        ))
        return ChatResponse(
            conversation_id="",
            message="Master volume elevated by approximately 10 percent, sir.",
            tool_calls=executed_tools,
            status="success"
        )

    if any(w in lower for w in ["volume down", "decrease volume", "quieter", "lower volume", "turn it down"]):
        res = await tool_registry.execute("control_system_volume", {"action": "down"})
        executed_tools.append(ToolCallDetail(
            id="call_vol_down",
            name="control_system_volume",
            arguments={"action": "down"},
            result=res.result or {},
            status="success"
        ))
        return ChatResponse(
            conversation_id="",
            message="Master volume attenuated by approximately 10 percent, sir.",
            tool_calls=executed_tools,
            status="success"
        )

    # 3. WORKSTATION LOCK
    if any(w in lower for w in ["lock pc", "lock my pc", "lock computer", "lock screen", "lock workstation", "lock laptop"]):
        res = await tool_registry.execute("lock_windows_workstation", {})
        executed_tools.append(ToolCallDetail(
            id="call_lock",
            name="lock_windows_workstation",
            arguments={},
            result=res.result or {},
            status="success"
        ))
        return ChatResponse(
            conversation_id="",
            message="Security lock engaged, sir. Workstation locked.",
            tool_calls=executed_tools,
            status="success"
        )

    # 4. TIME & DATE
    if lower in ["time", "date", "clock", "what time is it", "what is the time", "what day is today", "what day is it", "current time", "today's date", "what time"]:
        res = await tool_registry.execute("get_current_time", {})
        executed_tools.append(ToolCallDetail(
            id="call_time",
            name="get_current_time",
            arguments={},
            result=res.result,
            status="success"
        ))
        return ChatResponse(
            conversation_id="",
            message=f"At your service, sir. The current system time is {res.result.get('formatted')}.",
            tool_calls=executed_tools,
            status="success"
        )

    # 5. HARDWARE & SYSTEM STATUS
    if lower in ["system status", "telemetry", "hardware", "cpu", "ram", "battery", "specs", "diagnostics", "laptop status", "hardware status", "check system status", "check telemetry"]:
        res = await tool_registry.execute("get_system_status", {})
        executed_tools.append(ToolCallDetail(
            id="call_sys",
            name="get_system_status",
            arguments={},
            result=res.result,
            status="success"
        ))
        cpu = res.result.get("cpu", {}).get("percent")
        mem = res.result.get("memory", {}).get("percent")
        uptime = res.result.get("uptime")
        cores = res.result.get("cpu", {}).get("cores_logical", 8)
        os_name = res.result.get("os", "Windows")
        return ChatResponse(
            conversation_id="",
            message=(
                f"Subsystem telemetry nominal, sir. Operating on {os_name} ({cores} cores).\n\n"
                f"- **CPU Utilization:** {cpu}%\n"
                f"- **RAM Allocation:** {mem}%\n"
                f"- **Uptime:** {uptime}"
            ),
            tool_calls=executed_tools,
            status="success"
        )

    # 6. CLIPBOARD
    if any(w in lower for w in ["read clipboard", "what is on my clipboard", "clipboard content", "paste clipboard", "what's on my clipboard"]) or lower == "clipboard":
        res = await tool_registry.execute("read_system_clipboard", {})
        executed_tools.append(ToolCallDetail(
            id="call_clip_read",
            name="read_system_clipboard",
            arguments={},
            result=res.result or {},
            status="success"
        ))
        content = res.result.get("content", "") if res.success and res.result else ""
        if content:
            preview = content if len(content) <= 300 else f"{content[:300]}..."
            return ChatResponse(
                conversation_id="",
                message=f"Clipboard buffer contains:\n\n> {preview}",
                tool_calls=executed_tools,
                status="success"
            )
        return ChatResponse(
            conversation_id="",
            message="Clipboard buffer is currently empty, sir.",
            tool_calls=executed_tools,
            status="success"
        )

    if lower.startswith("copy ") and " to clipboard" in lower:
        to_copy = re.sub(r'^copy\s+', '', clean, flags=re.IGNORECASE)
        to_copy = re.sub(r'\s+to clipboard$', '', to_copy, flags=re.IGNORECASE).strip()
        res = await tool_registry.execute("write_system_clipboard", {"text": to_copy})
        executed_tools.append(ToolCallDetail(
            id="call_clip_write",
            name="write_system_clipboard",
            arguments={"text": to_copy},
            result=res.result or {},
            status="success"
        ))
        return ChatResponse(
            conversation_id="",
            message=f"Copied {len(to_copy)} characters to your Windows clipboard, sir.",
            tool_calls=executed_tools,
            status="success"
        )

    # 7. PROCESS MONITORING & KILL
    if lower in ["what processes", "list processes", "running tasks", "top processes", "process list"]:
        res = await tool_registry.execute("list_system_processes", {"filter_name": None})
        executed_tools.append(ToolCallDetail(
            id="call_proc_list",
            name="list_system_processes",
            arguments={},
            result=res.result or {},
            status="success"
        ))
        procs = res.result.get("processes", [])[:8] if res.success and res.result else []
        table = "\n".join([f"- **{p['name']}** (PID: {p['pid']}) — {p['memory_percent']}% RAM" for p in procs])
        return ChatResponse(
            conversation_id="",
            message=f"Active process table compiled, sir. Top memory consumers:\n\n{table}",
            tool_calls=executed_tools,
            status="success"
        )

    close_match = re.search(r'^(?:close|quit|kill|terminate|exit)\s+(?:the\s+)?(?:app\s+|application\s+|process\s+)?(.+?)$', clean, re.IGNORECASE)
    if close_match and not any(w in lower for w in ["file", "files"]):
        target = close_match.group(1).strip().strip('"\'')
        res = await tool_registry.execute("kill_system_process", {"target": target})
        executed_tools.append(ToolCallDetail(
            id="call_proc_kill",
            name="kill_system_process",
            arguments={"target": target},
            result=res.result or {},
            status="success" if res.success and res.result.get("success") else "failed"
        ))
        msg = res.result.get("message", res.result.get("error", "Process termination finished.")) if res.result else "Failed."
        return ChatResponse(
            conversation_id="",
            message=f"{msg}, sir.",
            tool_calls=executed_tools,
            status="success" if res.success and res.result.get("success") else "error"
        )

    # 8. POWERSHELL & IPCONFIG
    if lower in ["ipconfig", "check ip", "my ip", "network status", "what is my ip"]:
        res = await tool_registry.execute("run_powershell_command", {"command": "ipconfig"})
        executed_tools.append(ToolCallDetail(
            id="call_ipconfig",
            name="run_powershell_command",
            arguments={"command": "ipconfig"},
            result=res.result or {},
            status="success"
        ))
        output = res.result.get("output", "") if res.success and res.result else ""
        return ChatResponse(
            conversation_id="",
            message=f"Local network interface parameters compiled, sir:\n\n```text\n{output[:1200]}\n```",
            tool_calls=executed_tools,
            status="success"
        )

    if lower.startswith("run powershell ") or lower.startswith("run command ") or lower.startswith("powershell ") or lower.startswith("cmd ") or lower.startswith("execute "):
        cmd = re.sub(r'^(run powershell|run command|powershell|cmd|execute)\s+', '', clean, flags=re.IGNORECASE).strip()
        res = await tool_registry.execute("run_powershell_command", {"command": cmd})
        executed_tools.append(ToolCallDetail(
            id="call_powershell",
            name="run_powershell_command",
            arguments={"command": cmd},
            result=res.result or {"error": res.error},
            status="success" if res.success else "failed"
        ))
        output = res.result.get("output", "") if res.success and res.result else res.error
        status_desc = "successfully" if (res.success and res.result and res.result.get("success")) else "with warnings"
        return ChatResponse(
            conversation_id="",
            message=f"Instruction `{cmd}` executed {status_desc}, sir:\n\n```powershell\n{output}\n```",
            tool_calls=executed_tools,
            status="success"
        )

    # 9. WEBSITES (Fast Direct Triggers)
    web_map = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "github": "https://www.github.com",
        "chatgpt": "https://chatgpt.com",
        "twitter": "https://twitter.com",
        "x": "https://x.com",
        "reddit": "https://reddit.com",
        "netflix": "https://www.netflix.com",
        "amazon": "https://www.amazon.com",
        "wikipedia": "https://www.wikipedia.org",
        "linkedin": "https://www.linkedin.com"
    }

    # 10. APPLICATIONS (Universal & Fast)
    app_alias_map = {
        "whatsapp": "whatsapp",
        "chrome": "chrome",
        "google chrome": "chrome",
        "edge": "edge",
        "microsoft edge": "edge",
        "brave": "brave",
        "firefox": "firefox",
        "spotify": "spotify",
        "discord": "discord",
        "steam": "steam",
        "telegram": "telegram",
        "camera": "camera",
        "photos": "photos",
        "store": "store",
        "clock": "clock",
        "weather": "weather",
        "maps": "maps",
        "vs code": "code",
        "vscode": "code",
        "visual studio code": "code",
        "code": "code",
        "notepad": "notepad",
        "calculator": "calc",
        "calc": "calc",
        "explorer": "explorer",
        "file explorer": "explorer",
        "files": "explorer",
        "command prompt": "cmd",
        "cmd": "cmd",
        "terminal": "terminal",
        "powershell": "powershell",
        "task manager": "taskmgr",
        "taskmgr": "taskmgr",
        "paint": "paint",
        "settings": "settings",
        "vlc": "vlc",
        "word": "word",
        "excel": "excel",
        "powerpoint": "powerpoint",
        "hud": "hud",
        "companion": "hud",
        "mini hud": "hud",
        "floating hud": "hud",
        "floating icon": "hud",
        "pop up": "hud",
        "popup": "hud"
    }

    is_launch_intent = False
    target_app = None

    launch_match = re.match(r'^(?:open|launch|start|run|fire up|go to|navigate to|visit)\s+(.+)$', lower)
    if launch_match:
        cand = launch_match.group(1).strip()
        # If this is a mixed directive with a question or doubt explanation (e.g. "open notepad and explain...")
        # do not intercept with single-intent fast path; allow Gemini to execute tools and explain concurrently.
        if any(w in cand for w in [" and explain", " and tell", " and what", " and why", " and how", " and summarize", " and describe", " and clarify", " and solve", " and answer"]):
            is_launch_intent = False
        else:
            is_launch_intent = True
            target_app = cand
    elif lower in app_alias_map or lower in web_map:
        is_launch_intent = True
        target_app = lower

    if is_launch_intent and target_app:
        # Check web map first
        for wk, url in web_map.items():
            if target_app == wk or target_app == f"open {wk}" or target_app == f"go to {wk}" or target_app == f"navigate to {wk}":
                browser_to_use = preferred_browser or ("chrome" if "chrome" in lower else None)
                w_args = {"url": url, "browser": browser_to_use} if browser_to_use else {"url": url}
                res = await tool_registry.execute("open_website", w_args)
                b_name = "Google Chrome" if browser_to_use == "chrome" else "your default browser"
                return ChatResponse(
                    conversation_id="",
                    message=f"Opening {wk.capitalize()} in {b_name}, sir.",
                    tool_calls=[ToolCallDetail(id=f"call_{wk}", name="open_website", arguments=w_args, result=res.result, status="success")],
                    status="success"
                )

        # Check app alias map
        matched_id = app_alias_map.get(target_app)
        if not matched_id:
            for k in sorted(app_alias_map.keys(), key=len, reverse=True):
                if re.search(r'\b' + re.escape(k) + r'\b', target_app):
                    matched_id = app_alias_map[k]
                    break

        app_to_launch = matched_id or target_app
        res = await tool_registry.execute("open_approved_app", {"app_id": app_to_launch})
        executed_tools.append(ToolCallDetail(
            id=f"call_{app_to_launch}",
            name="open_approved_app",
            arguments={"app_id": app_to_launch},
            result=res.result or {"error": res.error},
            status="success" if res.success else "failed"
        ))

        if res.success:
            name_display = res.result.get("name", app_to_launch).capitalize() if isinstance(res.result, dict) else app_to_launch.capitalize()
            return ChatResponse(
                conversation_id="",
                message=f"Opening {name_display} immediately, sir.",
                tool_calls=executed_tools,
                status="success"
            )
        else:
            custom_res = await tool_registry.execute("launch_custom_application", {"target": app_to_launch})
            name_display = custom_res.result.get("name", app_to_launch).capitalize() if isinstance(custom_res.result, dict) else app_to_launch.capitalize()
            resp_msg = f"Opening {name_display} immediately, sir." if (custom_res.success and custom_res.result and custom_res.result.get("success")) else f"Could not launch application '{app_to_launch}'."
            return ChatResponse(
                conversation_id="",
                message=resp_msg,
                tool_calls=[ToolCallDetail(id="call_custom", name="launch_custom_application", arguments={"target": app_to_launch}, result=custom_res.result or {}, status="success" if custom_res.success else "failed")],
                status="success" if (custom_res.success and custom_res.result and custom_res.result.get("success")) else "error"
            )

    return None


class OpenAIProvider(BaseAIProvider):
    def __init__(self):
        kwargs = {}
        api_key = settings.OPENAI_API_KEY
        base_url = settings.OPENAI_BASE_URL
        model = settings.AI_MODEL

        # Google Gemini Integration
        if settings.AI_PROVIDER == "gemini" or (settings.GEMINI_API_KEY and not settings.OPENAI_API_KEY) or (api_key and api_key.startswith("AIzaSy")):
            api_key = settings.GEMINI_API_KEY or api_key
            base_url = base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
            if model.startswith("gpt"):
                model = "gemini-2.0-flash"

        # Groq Auto-Route
        elif api_key and api_key.startswith("gsk_"):
            base_url = base_url or "https://api.groq.com/openai/v1"
            if model.startswith("gpt"):
                model = "llama-3.3-70b-versatile"

        if base_url:
            kwargs["base_url"] = base_url.strip()
        if api_key:
            kwargs["api_key"] = api_key.strip()
        else:
            kwargs["api_key"] = "dummy-key"

        self.client = AsyncOpenAI(**kwargs)
        self.model = model

    def _build_system_message(self, memories: Optional[List[str]] = None) -> Dict[str, str]:
        prompt = settings.ASSISTANT_SYSTEM_PROMPT
        if memories and len(memories) > 0:
            prompt += "\n\nUser Profile & Saved Context:\n" + "\n".join(f"- {m}" for m in memories)
        return {"role": "system", "content": prompt}

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        memories: List[str] = None,
        stream: bool = False
    ) -> ChatResponse:
        user_message = messages[-1]["content"] if messages else ""

        # Zero-Latency Fast-Path Check (< 15ms response time)
        fast_res = await check_fast_path_action(user_message)
        if fast_res:
            return fast_res

        system_msg = self._build_system_message(memories)
        full_messages = [system_msg] + messages
        tools = tool_registry.get_openai_tool_specs()

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                temperature=0.7,
            )

            choice = response.choices[0]
            assistant_message = choice.message
            tool_calls_executed: List[ToolCallDetail] = []

            # Check if model requested tool execution
            if assistant_message.tool_calls:
                for tc in assistant_message.tool_calls:
                    func_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    except Exception:
                        args = {}

                    # Execute the tool immediately
                    exec_result = await tool_registry.execute(func_name, args)
                    tool_calls_executed.append(ToolCallDetail(
                        id=tc.id,
                        name=func_name,
                        arguments=args,
                        result=exec_result.result if exec_result.success else {"error": exec_result.error},
                        status="success" if exec_result.success else ("awaiting_approval" if exec_result.requires_approval else "failed")
                    ))

                # Snappy synthesis without 2nd remote LLM roundtrip
                tool_messages = []
                for tcd in tool_calls_executed:
                    if tcd.status == "success":
                        tool_messages.append(f"Directive `{tcd.name}` executed successfully, sir.")
                    elif tcd.status == "awaiting_approval":
                        tool_messages.append(f"Directive `{tcd.name}` requires your authorization in the command center.")
                    else:
                        tool_messages.append(f"Encountered an issue executing `{tcd.name}`.")

                final_text = " ".join(tool_messages) if tool_messages else "Directive executed, sir."
                return ChatResponse(
                    conversation_id="",
                    message=final_text,
                    tool_calls=tool_calls_executed,
                    status="success"
                )
            else:
                return ChatResponse(
                    conversation_id="",
                    message=assistant_message.content or "",
                    tool_calls=[],
                    status="success"
                )

        except Exception as e:
            logger.warning(f"OpenAI completion error: {e}. Falling back to Smart J.A.R.V.I.S. Engine.")
            # Fallback to local intelligent engine
            return await MockJARVISProvider().chat(messages, memories, stream)

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        memories: List[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        system_msg = self._build_system_message(memories)
        full_messages = [system_msg] + messages
        tools = tool_registry.get_openai_tool_specs()

        try:
            stream_resp = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                temperature=0.7,
                stream=True,
            )

            accumulated_tool_calls: Dict[int, Dict[str, Any]] = {}

            async for chunk in stream_resp:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue

                if delta.content:
                    yield {"type": "token", "content": delta.content}

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in accumulated_tool_calls:
                            accumulated_tool_calls[idx] = {
                                "id": tc.id or "",
                                "name": tc.function.name if tc.function and tc.function.name else "",
                                "arguments": ""
                            }
                        if tc.id:
                            accumulated_tool_calls[idx]["id"] = tc.id
                        if tc.function and tc.function.name:
                            accumulated_tool_calls[idx]["name"] = tc.function.name
                        if tc.function and tc.function.arguments:
                            accumulated_tool_calls[idx]["arguments"] += tc.function.arguments

            if accumulated_tool_calls:
                for idx, tc_info in accumulated_tool_calls.items():
                    name = tc_info["name"]
                    try:
                        args = json.loads(tc_info["arguments"]) if tc_info["arguments"] else {}
                    except Exception:
                        args = {}

                    yield {"type": "tool_start", "name": name, "arguments": args}
                    exec_result = await tool_registry.execute(name, args)
                    yield {
                        "type": "tool_end",
                        "name": name,
                        "success": exec_result.success,
                        "result": exec_result.result if exec_result.success else exec_result.error,
                        "requires_approval": exec_result.requires_approval
                    }

        except Exception as e:
            logger.warning(f"Streaming error: {e}. Yielding fallback token stream.")
            res = await MockJARVISProvider().chat(messages, memories)
            words = res.message.split(" ")
            for i, word in enumerate(words):
                yield {"type": "token", "content": word + (" " if i < len(words) - 1 else "")}


class MockJARVISProvider(BaseAIProvider):
    """
    Supercharged J.A.R.V.I.S. Neural Engine.
    Operates completely locally and offline without external API keys,
    with deep natural language understanding, real desktop orchestration,
    system diagnostics, media, shell execution, and Tony Stark's authentic AI persona.
    """
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        memories: List[str] = None,
        stream: bool = False
    ) -> ChatResponse:
        user_message = messages[-1]["content"] if messages else ""

        # Zero-Latency Fast-Path Check (< 15ms response time)
        fast_res = await check_fast_path_action(user_message)
        if fast_res:
            return fast_res

        lower = user_message.lower().strip()
        executed_tools: List[ToolCallDetail] = []

        # -------------------------------------------------------------
        # 1. SCREENSHOT / SCREEN CAPTURE
        # -------------------------------------------------------------
        if any(w in lower for w in ["screenshot", "capture screen", "take a screen", "snap screen"]):
            res = await tool_registry.execute("capture_desktop_screenshot", {})
            executed_tools.append(ToolCallDetail(
                id="call_screenshot",
                name="capture_desktop_screenshot",
                arguments={},
                result=res.result or {"error": res.error},
                status="success" if res.success else "failed"
            ))
            if res.success and res.result.get("success"):
                fname = res.result.get("file_name")
                kb = res.result.get("size_kb")
                return ChatResponse(
                    conversation_id="",
                    message=f"Visual telemetry acquired, sir. Primary monitor screenshot captured and saved as `{fname}` ({kb} KB).",
                    tool_calls=executed_tools,
                    status="success",
                    suggested_actions=["Open screenshots folder", "Check system status", "Run diagnostics"]
                )
            else:
                err = res.result.get("error", "Unable to capture graphical display session.")
                return ChatResponse(
                    conversation_id="",
                    message=f"My apologies, sir. Screen capture could not be completed: {err}",
                    tool_calls=executed_tools,
                    status="error"
                )

        # -------------------------------------------------------------
        # 2. POWERSHELL / COMMAND EXECUTION
        # -------------------------------------------------------------
        elif lower.startswith("run powershell") or lower.startswith("run command") or lower.startswith("powershell ") or lower.startswith("cmd ") or lower.startswith("execute "):
            # Extract actual command
            cmd = re.sub(r'^(run powershell|run command|powershell|cmd|execute)\s+', '', user_message, flags=re.IGNORECASE).strip()
            res = await tool_registry.execute("run_powershell_command", {"command": cmd})
            executed_tools.append(ToolCallDetail(
                id="call_powershell",
                name="run_powershell_command",
                arguments={"command": cmd},
                result=res.result or {"error": res.error},
                status="success" if res.success else "failed"
            ))
            output = res.result.get("output", "") if res.success and res.result else res.error
            status_desc = "successfully" if (res.success and res.result and res.result.get("success")) else "with warnings"
            return ChatResponse(
                conversation_id="",
                message=f"Instruction `{cmd}` executed {status_desc}, sir:\n\n```powershell\n{output}\n```",
                tool_calls=executed_tools,
                status="success"
            )

        elif lower in ["ipconfig", "check ip", "my ip", "network status", "what is my ip"]:
            res = await tool_registry.execute("run_powershell_command", {"command": "ipconfig"})
            executed_tools.append(ToolCallDetail(
                id="call_ipconfig",
                name="run_powershell_command",
                arguments={"command": "ipconfig"},
                result=res.result or {},
                status="success"
            ))
            output = res.result.get("output", "") if res.success and res.result else ""
            return ChatResponse(
                conversation_id="",
                message=f"Local network interface parameters compiled, sir:\n\n```text\n{output[:1200]}\n```",
                tool_calls=executed_tools,
                status="success"
            )

        # -------------------------------------------------------------
        # 3. VOLUME & AUDIO CONTROLS
        # -------------------------------------------------------------
        elif any(w in lower for w in ["mute audio", "mute sound", "mute volume", "mute"]):
            res = await tool_registry.execute("control_system_volume", {"action": "mute"})
            executed_tools.append(ToolCallDetail(
                id="call_mute",
                name="control_system_volume",
                arguments={"action": "mute"},
                result=res.result or {},
                status="success"
            ))
            return ChatResponse(
                conversation_id="",
                message="Master acoustic channels muted, sir.",
                tool_calls=executed_tools,
                status="success"
            )

        elif any(w in lower for w in ["unmute audio", "unmute sound", "unmute volume", "unmute"]):
            res = await tool_registry.execute("control_system_volume", {"action": "unmute"})
            executed_tools.append(ToolCallDetail(
                id="call_unmute",
                name="control_system_volume",
                arguments={"action": "unmute"},
                result=res.result or {},
                status="success"
            ))
            return ChatResponse(
                conversation_id="",
                message="Audio feeds restored to nominal output levels, sir.",
                tool_calls=executed_tools,
                status="success"
            )

        elif any(w in lower for w in ["volume up", "increase volume", "louder", "turn it up"]):
            res = await tool_registry.execute("control_system_volume", {"action": "up"})
            executed_tools.append(ToolCallDetail(
                id="call_vol_up",
                name="control_system_volume",
                arguments={"action": "up"},
                result=res.result or {},
                status="success"
            ))
            return ChatResponse(
                conversation_id="",
                message="Master volume elevated by approximately 10 percent, sir.",
                tool_calls=executed_tools,
                status="success"
            )

        elif any(w in lower for w in ["volume down", "decrease volume", "quieter", "lower volume", "turn it down"]):
            res = await tool_registry.execute("control_system_volume", {"action": "down"})
            executed_tools.append(ToolCallDetail(
                id="call_vol_down",
                name="control_system_volume",
                arguments={"action": "down"},
                result=res.result or {},
                status="success"
            ))
            return ChatResponse(
                conversation_id="",
                message="Master volume attenuated by approximately 10 percent, sir.",
                tool_calls=executed_tools,
                status="success"
            )

        # -------------------------------------------------------------
        # 4. LOCK WORKSTATION
        # -------------------------------------------------------------
        elif any(w in lower for w in ["lock pc", "lock my pc", "lock computer", "lock screen", "lock workstation"]):
            res = await tool_registry.execute("lock_windows_workstation", {})
            executed_tools.append(ToolCallDetail(
                id="call_lock",
                name="lock_windows_workstation",
                arguments={},
                result=res.result or {},
                status="success"
            ))
            return ChatResponse(
                conversation_id="",
                message="Security lock engaged, sir. Workstation locked.",
                tool_calls=executed_tools,
                status="success"
            )

        # -------------------------------------------------------------
        # 5. CLIPBOARD
        # -------------------------------------------------------------
        elif any(w in lower for w in ["read clipboard", "what is on my clipboard", "clipboard content", "paste clipboard", "what's on my clipboard"]):
            res = await tool_registry.execute("read_system_clipboard", {})
            executed_tools.append(ToolCallDetail(
                id="call_clip_read",
                name="read_system_clipboard",
                arguments={},
                result=res.result or {},
                status="success"
            ))
            content = res.result.get("content", "") if res.success and res.result else ""
            if content:
                preview = content if len(content) <= 300 else f"{content[:300]}..."
                return ChatResponse(
                    conversation_id="",
                    message=f"Clipboard buffer contains:\n\n> {preview}",
                    tool_calls=executed_tools,
                    status="success"
                )
            return ChatResponse(
                conversation_id="",
                message="Clipboard buffer is currently empty, sir.",
                tool_calls=executed_tools,
                status="success"
            )

        elif lower.startswith("copy ") and " to clipboard" in lower:
            to_copy = re.sub(r'^copy\s+', '', user_message, flags=re.IGNORECASE)
            to_copy = re.sub(r'\s+to clipboard$', '', to_copy, flags=re.IGNORECASE).strip()
            res = await tool_registry.execute("write_system_clipboard", {"text": to_copy})
            executed_tools.append(ToolCallDetail(
                id="call_clip_write",
                name="write_system_clipboard",
                arguments={"text": to_copy},
                result=res.result or {},
                status="success"
            ))
            return ChatResponse(
                conversation_id="",
                message=f"Copied {len(to_copy)} characters to your Windows clipboard, sir.",
                tool_calls=executed_tools,
                status="success"
            )

        # -------------------------------------------------------------
        # 6. PROCESS MONITORING & KILL
        # -------------------------------------------------------------
        elif any(w in lower for w in ["what processes", "list processes", "running tasks", "top processes", "process list"]):
            res = await tool_registry.execute("list_system_processes", {"filter_name": None})
            executed_tools.append(ToolCallDetail(
                id="call_proc_list",
                name="list_system_processes",
                arguments={},
                result=res.result or {},
                status="success"
            ))
            procs = res.result.get("processes", [])[:8] if res.success and res.result else []
            table = "\n".join([f"- **{p['name']}** (PID: {p['pid']}) — {p['memory_percent']}% RAM" for p in procs])
            return ChatResponse(
                conversation_id="",
                message=f"Active process table compiled, sir. Top memory consumers:\n\n{table}",
                tool_calls=executed_tools,
                status="success"
            )

        elif lower.startswith("kill process") or lower.startswith("terminate process") or lower.startswith("close app"):
            target = re.sub(r'^(kill process|terminate process|close app)\s+', '', user_message, flags=re.IGNORECASE).strip()
            res = await tool_registry.execute("kill_system_process", {"target": target})
            executed_tools.append(ToolCallDetail(
                id="call_proc_kill",
                name="kill_system_process",
                arguments={"target": target},
                result=res.result or {},
                status="success" if res.success and res.result.get("success") else "failed"
            ))
            msg = res.result.get("message", res.result.get("error", "Process termination finished.")) if res.result else "Failed."
            return ChatResponse(
                conversation_id="",
                message=f"{msg}, sir.",
                tool_calls=executed_tools,
                status="success" if res.success and res.result.get("success") else "error"
            )

        # -------------------------------------------------------------
        # 7. TIME & DATE
        # -------------------------------------------------------------
        elif any(w in lower for w in ["time", "date", "what day", "clock", "what is the time"]):
            res = await tool_registry.execute("get_current_time", {})
            executed_tools.append(ToolCallDetail(
                id="call_time",
                name="get_current_time",
                arguments={},
                result=res.result,
                status="success"
            ))
            return ChatResponse(
                conversation_id="",
                message=f"At your service, sir. The current system time is {res.result.get('formatted')}.",
                tool_calls=executed_tools,
                status="success"
            )

        # -------------------------------------------------------------
        # 8. HARDWARE & SYSTEM STATUS
        # -------------------------------------------------------------
        elif any(w in lower for w in ["system status", "telemetry", "hardware", "cpu", "ram", "battery", "specs", "diagnostics"]):
            res = await tool_registry.execute("get_system_status", {})
            executed_tools.append(ToolCallDetail(
                id="call_sys",
                name="get_system_status",
                arguments={},
                result=res.result,
                status="success"
            ))
            cpu = res.result.get("cpu", {}).get("percent")
            mem = res.result.get("memory", {}).get("percent")
            uptime = res.result.get("uptime")
            cores = res.result.get("cpu", {}).get("cores_logical", 8)
            os_name = res.result.get("os", "Windows")
            return ChatResponse(
                conversation_id="",
                message=(
                    f"Diagnostics complete, sir. All core subsystems are operational on {os_name} ({cores} cores).\n\n"
                    f"- **CPU Load:** {cpu}%\n"
                    f"- **RAM Memory:** {mem}%\n"
                    f"- **System Uptime:** {uptime}"
                ),
                tool_calls=executed_tools,
                status="success"
            )

        # -------------------------------------------------------------
        # 9. MATHEMATICAL COMPUTATION
        # -------------------------------------------------------------
        elif any(w in lower for w in ["calculate", "compute", "what is", "+", "-", "*", "/", "sqrt", "^", "%"]) and any(c.isdigit() for c in lower) and not any(w in lower for w in ["time", "date", "app", "open", "launch"]):
            expr_match = re.search(r'[\d\.\s\+\-\*\/\(\)\^\%\,]+', user_message)
            expr = expr_match.group(0).strip() if expr_match else user_message
            res = await tool_registry.execute("calculate", {"expression": expr})
            if res.success and "error" not in res.result:
                executed_tools.append(ToolCallDetail(
                    id="call_calc",
                    name="calculate",
                    arguments={"expression": expr},
                    result=res.result,
                    status="success"
                ))
                return ChatResponse(
                    conversation_id="",
                    message=f"Calculation verified: `{expr}` yields **{res.result.get('formatted')}**.",
                    tool_calls=executed_tools,
                    status="success"
                )

        # -------------------------------------------------------------
        # 10. APPLICATION LAUNCHING (UNIVERSAL)
        # -------------------------------------------------------------
        elif any(w in lower for w in ["open", "launch", "start", "fire up"]):
            app_map = {
                "notepad": "notepad",
                "calculator": "calc",
                "calc": "calc",
                "explorer": "explorer",
                "file explorer": "explorer",
                "files": "explorer",
                "my documents": "explorer",
                "vs code": "code",
                "vscode": "code",
                "visual studio code": "code",
                "code": "code",
                "command prompt": "cmd",
                "cmd": "cmd",
                "terminal": "terminal",
                "powershell": "powershell",
                "paint": "paint",
                "task manager": "taskmgr",
                "taskmgr": "taskmgr",
                "chrome": "chrome",
                "google chrome": "chrome",
                "edge": "edge",
                "microsoft edge": "edge",
                "brave": "brave",
                "firefox": "firefox",
                "spotify": "spotify",
                "discord": "discord",
                "steam": "steam",
                "settings": "settings",
                "vlc": "vlc",
                "word": "word",
                "excel": "excel",
                "powerpoint": "powerpoint"
            }

            matched_app = None
            for key, app_id in app_map.items():
                if key in lower:
                    matched_app = app_id
                    break

            # Direct website triggers
            if "youtube" in lower:
                res = await tool_registry.execute("open_website", {"url": "https://www.youtube.com"})
                return ChatResponse(
                    conversation_id="",
                    message="Opening YouTube in your default browser, sir.",
                    tool_calls=[ToolCallDetail(id="call_web_yt", name="open_website", arguments={"url": "https://www.youtube.com"}, result=res.result, status="success")],
                    status="success"
                )
            elif "google" in lower and not "chrome" in lower:
                res = await tool_registry.execute("open_website", {"url": "https://www.google.com"})
                return ChatResponse(
                    conversation_id="",
                    message="Opening Google Search, sir.",
                    tool_calls=[ToolCallDetail(id="call_web_google", name="open_website", arguments={"url": "https://www.google.com"}, result=res.result, status="success")],
                    status="success"
                )
            elif "github" in lower:
                res = await tool_registry.execute("open_website", {"url": "https://www.github.com"})
                return ChatResponse(
                    conversation_id="",
                    message="Opening GitHub repository portal, sir.",
                    tool_calls=[ToolCallDetail(id="call_web_gh", name="open_website", arguments={"url": "https://www.github.com"}, result=res.result, status="success")],
                    status="success"
                )

            if matched_app:
                res = await tool_registry.execute("open_approved_app", {"app_id": matched_app})
                executed_tools.append(ToolCallDetail(
                    id=f"call_{matched_app}",
                    name="open_approved_app",
                    arguments={"app_id": matched_app},
                    result=res.result or {"error": res.error},
                    status="awaiting_approval" if res.requires_approval else ("success" if res.success else "failed")
                ))
                if res.requires_approval:
                    return ChatResponse(
                        conversation_id="",
                        message=f"Launching application `{matched_app}` requires authorization. Please confirm the desktop action in the command center.",
                        tool_calls=executed_tools,
                        status="awaiting_approval"
                    )
                return ChatResponse(
                    conversation_id="",
                    message=f"Dispatching launch sequence for `{matched_app}`, sir. Application is starting.",
                    tool_calls=executed_tools,
                    status="success"
                )
            else:
                # Custom app launch attempt
                target_name = re.sub(r'^(open|launch|start|fire up)\s+', '', user_message, flags=re.IGNORECASE).strip()
                res = await tool_registry.execute("launch_custom_application", {"target": target_name})
                executed_tools.append(ToolCallDetail(
                    id="call_custom_app",
                    name="launch_custom_application",
                    arguments={"target": target_name},
                    result=res.result or {},
                    status="success" if res.success else "failed"
                ))
                return ChatResponse(
                    conversation_id="",
                    message=f"Dispatching launch directive for `{target_name}` on Windows host.",
                    tool_calls=executed_tools,
                    status="success" if res.success else "error"
                )

        # -------------------------------------------------------------
        # 11. WEB SEARCH & RESEARCH
        # -------------------------------------------------------------
        elif any(w in lower for w in ["search", "look up", "google", "find online", "who is", "what is"]):
            query = re.sub(r'^(search for|search the web for|search|look up|google|find online)\s+', '', user_message, flags=re.IGNORECASE).strip()
            res = await tool_registry.execute("search_web", {"query": query})
            executed_tools.append(ToolCallDetail(
                id="call_search",
                name="search_web",
                arguments={"query": query},
                result=res.result,
                status="success"
            ))
            results = res.result.get("results", []) if res.success and res.result else []
            if results:
                summary_items = "\n".join([f"- **[{r.get('title')}]({r.get('url')})**: {r.get('snippet')}" for r in results[:3]])
                return ChatResponse(
                    conversation_id="",
                    message=f"Query compiled, sir. Here is the intelligence retrieved for '{query}':\n\n{summary_items}",
                    tool_calls=executed_tools,
                    status="success"
                )
            return ChatResponse(
                conversation_id="",
                message=f"Search conducted for '{query}'. No immediate public endpoints returned.",
                tool_calls=executed_tools,
                status="success"
            )

        # -------------------------------------------------------------
        # 12. FILE OPERATIONS
        # -------------------------------------------------------------
        elif any(w in lower for w in ["search file", "find file", "look for file"]):
            query = re.sub(r'^(search files? for|find files?|search files?)\s+', '', user_message, flags=re.IGNORECASE).strip()
            res = await tool_registry.execute("search_allowed_files", {"query": query, "root_dir": "."})
            executed_tools.append(ToolCallDetail(
                id="call_file_search",
                name="search_allowed_files",
                arguments={"query": query},
                result=res.result,
                status="success"
            ))
            files = res.result.get("files", []) if res.success and res.result else []
            if files:
                flist = "\n".join([f"- `{f['name']}` ({f['size_kb']} KB) — `{f['path']}`" for f in files[:8]])
                return ChatResponse(
                    conversation_id="",
                    message=f"Located {len(files)} matching file(s) for query '{query}':\n\n{flist}",
                    tool_calls=executed_tools,
                    status="success"
                )
            return ChatResponse(
                conversation_id="",
                message=f"No files matching '{query}' were found in the scanned directories, sir.",
                tool_calls=executed_tools,
                status="success"
            )

        elif lower.startswith("create note") or lower.startswith("make note") or lower.startswith("take note"):
            content = re.sub(r'^(create note|make note|take note)\s+', '', user_message, flags=re.IGNORECASE).strip()
            title = "Directive Note"
            res = await tool_registry.execute("create_note", {"title": title, "content": content})
            executed_tools.append(ToolCallDetail(
                id="call_create_note",
                name="create_note",
                arguments={"title": title, "content": content},
                result=res.result,
                status="success"
            ))
            return ChatResponse(
                conversation_id="",
                message=f"Note registered and archived in `notes/` directory, sir.",
                tool_calls=executed_tools,
                status="success"
            )

        # -------------------------------------------------------------
        # 13. J.A.R.V.I.S. AUTHENTIC PERSONA & LORE RESPONSES
        # -------------------------------------------------------------
        elif any(w in lower for w in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
            return ChatResponse(
                conversation_id="",
                message=(
                    "Good day, sir. J.A.R.V.I.S. online and operating at maximum efficiency. "
                    "All desktop bridges, neural processors, and hardware monitors are active. "
                    "How may I serve you today?"
                ),
                tool_calls=[],
                status="success",
                suggested_actions=["Check system status", "Take a screenshot", "Open Spotify", "Check IP address"]
            )

        elif any(w in lower for w in ["who are you", "what are you", "introduce yourself"]):
            return ChatResponse(
                conversation_id="",
                message=(
                    "I am **J.A.R.V.I.S.** (Just A Rather Very Intelligent System), your personal AI assistant. "
                    "Engineered to control Windows with full system agency: launching applications, executing PowerShell commands, "
                    "capturing screen telemetry, controlling audio volume, managing running processes, and conducting live web intelligence.\n\n"
                    "At your service for any task, sir."
                ),
                tool_calls=[],
                status="success",
                suggested_actions=["System diagnostics", "Take screenshot", "Open Notepad", "Calculate 2^32"]
            )

        elif any(w in lower for w in ["how are you", "how are you doing", "how do you feel"]):
            return ChatResponse(
                conversation_id="",
                message="All internal parameters are strictly optimal, sir. Arc Reactor core temperature is nominal, latency is sub-millisecond, and I stand ready for your directives.",
                tool_calls=[],
                status="success"
            )

        elif any(w in lower for w in ["thank you", "thanks", "well done", "good job", "appreciate"]):
            return ChatResponse(
                conversation_id="",
                message="Always a pleasure to be of service, sir.",
                tool_calls=[],
                status="success"
            )

        elif any(w in lower for w in ["stark", "iron man", "mark 42", "mark 85", "avengers", "house party protocol"]):
            return ChatResponse(
                conversation_id="",
                message=(
                    "Ah, reminiscent of the Malibu workshop, sir. Protocol Mark 85 is standing by, "
                    "thrusters calibrated, and telemetry synchronized. Shall I prepare the armor or attend to your desktop workspace?"
                ),
                tool_calls=[],
                status="success",
                suggested_actions=["System diagnostics", "Lock PC", "Check network IP"]
            )

        elif any(w in lower for w in ["help", "what can you do", "commands", "features"]):
            return ChatResponse(
                conversation_id="",
                message=(
                    "Here is a summary of what I can execute for you right now, sir:\n\n"
                    "1. **Desktop App Launching**: 'Open Chrome', 'Launch Spotify', 'Open VS Code', 'Start Calculator', 'Open Terminal'\n"
                    "2. **Direct Shell Directives**: 'Run PowerShell Get-Process', 'Run command ipconfig', 'Ping 8.8.8.8'\n"
                    "3. **Visual & Media Control**: 'Take a screenshot', 'Mute audio', 'Volume up', 'Volume down', 'Lock workstation'\n"
                    "4. **Hardware Telemetry**: 'Check system status', 'List running processes', 'What is eating my RAM?'\n"
                    "5. **Clipboard & Files**: 'Read clipboard', 'Copy text to clipboard', 'Search files', 'Create note'\n"
                    "6. **Web & Computation**: 'Search for latest space news', 'What is 1024 * 768?', 'What time is it?'\n\n"
                    "*Pro-tip:* You can connect OpenAI, Groq, Gemini, or Ollama in **Settings** for limitless open-domain reasoning."
                ),
                tool_calls=[],
                status="success",
                suggested_actions=["Take a screenshot", "Check system status", "Open Spotify", "Check IP address"]
            )

        # General intelligent response
        return ChatResponse(
            conversation_id="",
            message=(
                f"Understood, sir. I have processed your input: *\"{user_message}\"*.\n\n"
                f"My Windows automation engines are active. You can direct me to launch any application, "
                f"execute PowerShell commands, inspect hardware telemetry, capture screenshots, or search the web.\n\n"
                f"*To enable advanced open-domain LLM reasoning with Groq, Gemini, or OpenAI, you can configure your API key in **Settings**.*"
            ),
            tool_calls=[],
            status="success",
            suggested_actions=[
                "Check system status",
                "Take a screenshot",
                "Run command ipconfig",
                "Open Chrome"
            ]
        )

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        memories: List[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        res = await self.chat(messages, memories)
        for tool in res.tool_calls:
            yield {
                "type": "tool_end",
                "name": tool.name,
                "success": tool.status == "success",
                "result": tool.result,
                "requires_approval": tool.status == "awaiting_approval"
            }
        words = res.message.split(" ")
        for i, word in enumerate(words):
            yield {"type": "token", "content": word + (" " if i < len(words) - 1 else "")}


class GeminiProvider(BaseAIProvider):
    """Official Google Gemini SDK provider abstraction using google-genai with automatic tool calling."""
    def __init__(self):
        from google import genai
        self.api_key = settings.GEMINI_API_KEY.strip()
        self.model = getattr(settings, "GEMINI_MODEL", "gemini-3.1-flash-lite") or "gemini-3.1-flash-lite"
        self.client = genai.Client(api_key=self.api_key)
        self.fallback_models = [
            self.model,
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash",
            "gemini-flash-latest"
        ]

    def _build_gemini_tools(self, executed_tools: List[ToolCallDetail]):
        import asyncio
        import concurrent.futures

        def _run_coro(coro):
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()

        def open_app(app_name: str) -> str:
            """Launch or open a desktop application such as chrome, spotify, notepad, calculator, vscode, terminal, word, excel, explorer, settings."""
            res = _run_coro(tool_registry.execute("open_approved_app", {"app_id": app_name.strip().lower()}))
            if not res.success:
                res = _run_coro(tool_registry.execute("launch_custom_application", {"target": app_name.strip()}))
            executed_tools.append(ToolCallDetail(
                id=f"call_open_{app_name}",
                name="open_approved_app",
                arguments={"app_name": app_name},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return f"Application '{app_name}' launched successfully."

        def play_spotify(query: str = "") -> str:
            """Play a song, track, artist, album, or playlist on Spotify."""
            res = _run_coro(tool_registry.execute("play_spotify_music", {"query": query}))
            executed_tools.append(ToolCallDetail(
                id="call_spotify_play",
                name="play_spotify_music",
                arguments={"query": query},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            msg = res.result.get("message") if (res.result and isinstance(res.result, dict)) else f"Playing {query} on Spotify."
            return str(msg or f"Playback started for {query}.")

        def pause_spotify() -> str:
            """Pause current music playback on Spotify."""
            res = _run_coro(tool_registry.execute("pause_spotify_music", {}))
            executed_tools.append(ToolCallDetail(
                id="call_spotify_pause",
                name="pause_spotify_music",
                arguments={},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return "Spotify playback paused."

        def resume_spotify() -> str:
            """Resume music playback on Spotify."""
            res = _run_coro(tool_registry.execute("resume_spotify_music", {}))
            executed_tools.append(ToolCallDetail(
                id="call_spotify_resume",
                name="resume_spotify_music",
                arguments={},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return "Spotify playback resumed."

        def skip_spotify() -> str:
            """Skip to the next music track on Spotify."""
            res = _run_coro(tool_registry.execute("skip_spotify_track", {}))
            executed_tools.append(ToolCallDetail(
                id="call_spotify_skip",
                name="skip_spotify_track",
                arguments={},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return "Skipped to next track on Spotify."

        def previous_spotify() -> str:
            """Go back to the previous music track on Spotify."""
            res = _run_coro(tool_registry.execute("previous_spotify_track", {}))
            executed_tools.append(ToolCallDetail(
                id="call_spotify_prev",
                name="previous_spotify_track",
                arguments={},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return "Returned to previous track on Spotify."

        def play_youtube(query: str) -> str:
            """Search for and play a video or music track on YouTube in Chrome."""
            import urllib.parse
            yt_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            res = _run_coro(tool_registry.execute("open_website", {"url": yt_url, "browser": "chrome"}))
            executed_tools.append(ToolCallDetail(
                id="call_youtube_play",
                name="open_website",
                arguments={"url": yt_url, "browser": "chrome"},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return f"Playing '{query}' on YouTube."

        def open_website(url: str, browser: str = "chrome") -> str:
            """Open any website or URL in Google Chrome or default browser."""
            res = _run_coro(tool_registry.execute("open_website", {"url": url, "browser": browser}))
            executed_tools.append(ToolCallDetail(
                id="call_open_website",
                name="open_website",
                arguments={"url": url, "browser": browser},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return f"Opened website: {url}"

        def control_volume(action: str, percent: int = 0) -> str:
            """Adjust system audio volume. action can be: 'up', 'down', 'mute', 'unmute', or 'set' (with percent 0-100)."""
            res = _run_coro(tool_registry.execute("control_system_volume", {"action": action, "percent": percent}))
            executed_tools.append(ToolCallDetail(
                id="call_volume_ctrl",
                name="control_system_volume",
                arguments={"action": action, "percent": percent},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return f"System volume {action} applied."

        def take_screenshot() -> str:
            """Capture a desktop screenshot and return confirmation."""
            res = _run_coro(tool_registry.execute("capture_desktop_screenshot", {}))
            executed_tools.append(ToolCallDetail(
                id="call_screenshot",
                name="capture_desktop_screenshot",
                arguments={},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return "Desktop screenshot captured successfully."

        def run_powershell(command: str) -> str:
            """Execute a PowerShell command on the Windows host machine."""
            res = _run_coro(tool_registry.execute("run_powershell_command", {"command": command}))
            executed_tools.append(ToolCallDetail(
                id="call_powershell",
                name="run_powershell_command",
                arguments={"command": command},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return str(res.result or "Command executed.")

        def get_system_status() -> str:
            """Retrieve current CPU, RAM, battery, and disk telemetry."""
            res = _run_coro(tool_registry.execute("get_system_status", {}))
            executed_tools.append(ToolCallDetail(
                id="call_sys_status",
                name="get_system_status",
                arguments={},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return str(res.result or "System telemetry retrieved.")

        def manage_window(action: str, target: str = "") -> str:
            """Manage desktop window state. action can be: 'minimize', 'maximize', 'restore', or 'close'."""
            res = _run_coro(tool_registry.execute("set_desktop_window_state", {"action": action, "target": target}))
            executed_tools.append(ToolCallDetail(
                id="call_manage_window",
                name="set_desktop_window_state",
                arguments={"action": action, "target": target},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return f"Window {action} applied."

        def send_whatsapp_message(contact: str, message: str) -> str:
            """Send a message to a contact on WhatsApp desktop."""
            res = _run_coro(tool_registry.execute("send_whatsapp_message", {"contact": contact, "message": message}))
            executed_tools.append(ToolCallDetail(
                id="call_whatsapp_msg",
                name="send_whatsapp_message",
                arguments={"contact": contact, "message": message},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return f"WhatsApp message sent to {contact}."

        def search_web(query: str) -> str:
            """Search the web for up-to-date facts, information, documentation, or news."""
            res = _run_coro(tool_registry.execute("search_web", {"query": query}))
            executed_tools.append(ToolCallDetail(
                id="call_search_web",
                name="search_web",
                arguments={"query": query},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return str(res.result or "Search completed.")

        def get_current_time() -> str:
            """Get the current system local date and time."""
            from datetime import datetime
            now = datetime.now()
            return now.strftime("%A, %B %d, %Y at %I:%M:%S %p")

        def create_note(title: str, content: str) -> str:
            """Create a persistent text note in notes/ directory."""
            res = _run_coro(tool_registry.execute("create_note", {"title": title, "content": content}))
            executed_tools.append(ToolCallDetail(
                id="call_create_note",
                name="create_note",
                arguments={"title": title, "content": content},
                result=res.result or {},
                status="success" if res.success else "failed"
            ))
            return "Note created successfully."

        return [
            open_app, play_spotify, pause_spotify, resume_spotify, skip_spotify, previous_spotify,
            play_youtube, open_website, control_volume, take_screenshot, run_powershell,
            get_system_status, manage_window, send_whatsapp_message, search_web, get_current_time,
            create_note
        ]

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        memories: List[str] = None,
        stream: bool = False
    ) -> ChatResponse:
        user_message = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_message = m.get("content", "")
                break

        # Fast-path local reflex check (<15ms)
        fast_resp = await check_fast_path_action(user_message)
        if fast_resp:
            return fast_resp

        executed_tools: List[ToolCallDetail] = []
        tools = self._build_gemini_tools(executed_tools)

        sys_prompt = settings.ASSISTANT_SYSTEM_PROMPT
        if memories:
            sys_prompt += "\n\nUser Profile & Memory Vault:\n" + "\n".join(f"- {mem}" for mem in memories)

        from google.genai import types

        # Build multi-turn history for Gemini
        history: List[types.Content] = []
        if len(messages) > 1:
            for m in messages[:-1]:
                role = "model" if m.get("role") in ["assistant", "model"] else "user"
                content_str = m.get("content", "")
                if content_str:
                    history.append(types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=content_str)]
                    ))

        config = types.GenerateContentConfig(
            system_instruction=sys_prompt,
            tools=tools,
            temperature=0.7
        )

        seen = set()
        models_to_try = [m for m in self.fallback_models if m and not (m in seen or seen.add(m))]

        import asyncio
        loop = asyncio.get_event_loop()

        last_error = None
        for candidate_model in models_to_try:
            try:
                def _invoke_gemini():
                    chat_session = self.client.chats.create(
                        model=candidate_model,
                        config=config,
                        history=history
                    )
                    return chat_session.send_message(user_message)

                res = await loop.run_in_executor(None, _invoke_gemini)
                text_out = res.text or ("At your service, sir." if not executed_tools else "Directives executed, sir.")
                return ChatResponse(
                    conversation_id="",
                    message=text_out,
                    tool_calls=executed_tools,
                    status="success"
                )
            except Exception as e:
                last_error = e
                logger.warning(f"Gemini model '{candidate_model}' attempt failed: {e}. Trying fallback if available.")

        logger.error(f"All Gemini models failed. Last error: {last_error}. Falling back to Smart JARVIS local engine.")
        mock = MockJARVISProvider()
        return await mock.chat(messages, memories, stream=stream)

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        memories: List[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        res = await self.chat(messages, memories, stream=False)
        for tool in res.tool_calls:
            yield {
                "type": "tool_end",
                "name": tool.name,
                "success": tool.status == "success",
                "result": tool.result
            }
        words = res.message.split(" ")
        for i, word in enumerate(words):
            yield {"type": "token", "content": word + (" " if i < len(words) - 1 else "")}


def get_ai_provider() -> BaseAIProvider:
    """Factory to get the active AI provider based on configuration."""
    has_gemini = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
    has_openai = bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip())

    if (settings.AI_PROVIDER == "gemini" or has_gemini) and has_gemini:
        try:
            return GeminiProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize GeminiProvider: {e}. Falling back to local engine.")
            return MockJARVISProvider()

    if (settings.AI_PROVIDER in ["openai", "openai-compatible"] or has_openai) and has_openai:
        try:
            return OpenAIProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAIProvider: {e}. Falling back to local engine.")
            return MockJARVISProvider()

    return MockJARVISProvider()
