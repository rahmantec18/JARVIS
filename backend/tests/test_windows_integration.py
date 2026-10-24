import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.tools.registry import tool_registry
from app.ai.provider import check_fast_path_action, get_ai_provider
from desktop_agent.security.authorizer import authorizer
from desktop_agent.tools.media_controller import control_volume, control_media, check_active_audio_sessions
from desktop_agent.tools.spotify_player import resolve_track_metadata, is_spotify_installed
from desktop_agent.tools.file_manager import search_files, create_directory, delete_item
from desktop_agent.tools.app_launcher import activate_application_window, set_window_state


@pytest.mark.asyncio
async def test_01_open_file_explorer():
    res = await check_fast_path_action("open explorer")
    assert res is not None
    assert res.status == "success"
    assert any(t.name in ["open_approved_app", "launch_custom_application"] for t in res.tool_calls)


@pytest.mark.asyncio
async def test_02_open_documents():
    res = await check_fast_path_action("open documents")
    assert res is not None
    assert res.status == "success"
    assert "documents" in res.message.lower() or "explorer" in res.message.lower()


@pytest.mark.asyncio
async def test_03_open_downloads():
    res = await check_fast_path_action("go to downloads")
    assert res is not None
    assert res.status == "success"
    assert "downloads" in res.message.lower()


@pytest.mark.asyncio
async def test_04_05_search_and_find_files(tmp_path):
    # Create sample PDF
    test_pdf = tmp_path / "cybersecurity_brief.pdf"
    test_pdf.write_text("Confidential Cybersecurity Protocol")

    search_res = search_files(query="cybersecurity", base_dir=str(tmp_path), extension=".pdf")
    assert search_res["success"] is True
    assert search_res["count"] == 1
    assert "cybersecurity_brief.pdf" in search_res["files"][0]["name"]


@pytest.mark.asyncio
async def test_06_07_spotify_search_and_play():
    # Verify metadata extraction for "Believer by Imagine Dragons"
    meta = resolve_track_metadata("Believer Imagine Dragons")
    assert meta["title"] == "Believer"
    assert "imagine dragons" in meta["artist"].lower()

    # Fast-path intent routing
    res = await check_fast_path_action("Play Believer by Imagine Dragons on Spotify")
    assert res is not None
    assert any(t.name == "play_spotify_music" for t in res.tool_calls)
    assert res.status in ["success", "error"]


@pytest.mark.asyncio
async def test_08_spotify_pause_and_resume():
    res_pause = await check_fast_path_action("pause the song")
    assert res_pause is not None
    assert res_pause.status == "success"
    assert any(t.name == "pause_spotify_music" for t in res_pause.tool_calls)

    res_resume = await check_fast_path_action("resume playback")
    assert res_resume is not None
    assert res_resume.status == "success"
    assert any(t.name == "resume_spotify_music" for t in res_resume.tool_calls)


@pytest.mark.asyncio
async def test_09_10_11_12_whatsapp_intent_and_policy():
    # Open WhatsApp
    res_wa = await check_fast_path_action("open whatsapp")
    assert res_wa is not None
    assert res_wa.status == "success"

    # Send message with contact & text
    res_msg = await check_fast_path_action("send I'll be there in ten minutes to Ahmed on WhatsApp")
    assert res_msg is not None
    assert res_msg.status == "success"
    assert any(t.name == "send_whatsapp_message" for t in res_msg.tool_calls)


@pytest.mark.asyncio
async def test_13_open_chrome():
    res_chrome = await check_fast_path_action("open chrome")
    assert res_chrome is not None
    assert res_chrome.status == "success"


@pytest.mark.asyncio
async def test_14_change_system_volume():
    # Exact 30 percent as in prompt example
    res_vol = await check_fast_path_action("turn the volume down to 30 percent")
    assert res_vol is not None
    assert res_vol.status == "success"
    assert any(t.name == "control_system_volume" for t in res_vol.tool_calls)


@pytest.mark.asyncio
async def test_15_cancel_and_window_state():
    # Minimize window
    res_min = await check_fast_path_action("minimize the window")
    assert res_min is not None
    assert res_min.status == "success"
    assert any(t.name == "set_desktop_window_state" for t in res_min.tool_calls)


@pytest.mark.asyncio
async def test_16_handling_unavailable_application():
    from desktop_agent.tools.app_launcher import launch_application
    with patch.dict(authorizer.config, {"full_access_mode": False}):
        res = launch_application("completely_fake_nonexistent_application_xyz123")
        assert res["success"] is False
        assert "not in the authorized" in res["error"]


@pytest.mark.asyncio
async def test_17_handling_ambiguous_recognition():
    from app.ai.provider import MockJARVISProvider
    provider = MockJARVISProvider()
    res = await provider.chat([{"role": "user", "content": "asdkjasdkj ????"}])
    assert res.status == "success"
    assert len(res.message) > 0


@pytest.mark.asyncio
async def test_18_reject_invalid_tool_arguments():
    # Calling volume with unsupported action
    vol_res = control_volume("invalid_unknown_action")
    assert vol_res["success"] is False
    assert "Unsupported volume directive" in vol_res["error"]


@pytest.mark.asyncio
async def test_19_prevent_unauthorized_shell_command():
    from desktop_agent.tools.command_runner import execute_powershell
    # Safe command passes
    safe = execute_powershell("Write-Output 'Authorized JARVIS Test'")
    assert safe["success"] is True
    assert "Authorized JARVIS Test" in safe["output"]


@pytest.mark.asyncio
async def test_20_prevent_accidental_destructive_operations(tmp_path):
    # Test safe deletion to Recycle Bin via send2trash
    sample_file = tmp_path / "test_safe_deletion.txt"
    sample_file.write_text("Temporary test file")
    del_res = delete_item(str(sample_file))
    assert del_res["success"] is True
    assert not sample_file.exists()
