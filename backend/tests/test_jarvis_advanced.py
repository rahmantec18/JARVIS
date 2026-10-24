import pytest
from app.assistant.planner import MultiStepPlanner, ExecutionStep
from app.assistant.intent_router import (
    parse_tamil_directive,
    parse_spotify_directive,
    parse_volume_directive,
    parse_window_state_directive
)
from desktop_agent.tools.media_controller import control_volume, control_media
from desktop_agent.tools.spotify_player import resolve_track_metadata, is_spotify_installed
from desktop_agent.tools.file_manager import search_files, create_directory, rename_item, copy_item, move_item


def test_tamil_intent_parsing():
    # WhatsApp open pannu
    res = parse_tamil_directive("WhatsApp open pannu")
    assert res is not None
    assert res[0] == "open_app"
    assert res[1]["app"] == "whatsapp"

    # Spotify open pannu
    res2 = parse_tamil_directive("Spotify open pannu")
    assert res2 is not None
    assert res2[0] == "open_app"
    assert res2[1]["app"] == "spotify"

    # Play pannu
    res3 = parse_tamil_directive("Believer play pannu")
    assert res3 is not None
    assert res3[0] == "play_spotify"
    assert "believer" in res3[1]["query"].lower()

    # Volume controls
    res4 = parse_tamil_directive("volume koraikkavum")
    assert res4 is not None
    assert res4[0] == "control_volume"
    assert res4[1]["action"] == "down"


def test_spotify_intent_parsing():
    # Song play directive
    res = parse_spotify_directive("Play Believer by Imagine Dragons")
    assert res is not None
    assert res[0] == "play_spotify"
    assert "believer" in res[1]["query"].lower()

    # Open and play directive (User command format)
    res_open = parse_spotify_directive("open Spotify and play some song")
    assert res_open is not None
    assert res_open[0] == "play_spotify"
    assert res_open[1]["query"] == "some song"

    # Playlist play directive
    res2 = parse_spotify_directive("play my workout playlist")
    assert res2 is not None
    assert res2[0] == "play_spotify"
    assert res2[1]["playlist"] is True

    # Playback transport
    assert parse_spotify_directive("pause")[0] == "pause_spotify"
    assert parse_spotify_directive("resume")[0] == "resume_spotify"
    assert parse_spotify_directive("skip this song")[0] == "skip_spotify"
    assert parse_spotify_directive("previous track")[0] == "previous_spotify"


def test_youtube_intent_parsing():
    from app.assistant.intent_router import parse_youtube_directive
    res = parse_youtube_directive("open YouTube and play despacito song")
    assert res is not None
    assert res[0] == "play_youtube"
    assert "despacito" in res[1]["query"].lower()

    res2 = parse_youtube_directive("play Believer on YouTube")
    assert res2 is not None
    assert res2[0] == "play_youtube"
    assert "believer" in res2[1]["query"].lower()


@pytest.mark.asyncio
async def test_no_step_one_step_two_in_plan():
    from app.assistant.planner import ExecutionStep, MultiStepPlanner
    steps = [
        ExecutionStep(step_number=1, instruction="open chrome"),
        ExecutionStep(step_number=2, instruction="minimize chrome")
    ]
    res = await MultiStepPlanner.execute_plan(steps)
    assert "step 1" not in res.message.lower()
    assert "step 2" not in res.message.lower()
    assert "multi-action directive executed" not in res.message.lower()


def test_volume_intent_parsing():
    # Exact percentage
    res1 = parse_volume_directive("Turn the volume down to 30 percent")
    assert res1 is not None
    assert res1[0] == "control_volume"
    assert res1[1]["action"] == "set"
    assert res1[1]["level"] == 30

    res2 = parse_volume_directive("Set volume to 50%")
    assert res2 is not None
    assert res2[1]["level"] == 50

    # Relative volume
    res3 = parse_volume_directive("Volume up")
    assert res3 is not None
    assert res3[1]["action"] == "up"

    res4 = parse_volume_directive("Mute audio")
    assert res4 is not None
    assert res4[1]["action"] == "mute"


def test_window_state_parsing():
    res = parse_window_state_directive("Minimize the window")
    assert res is not None
    assert res[0] == "set_window_state"
    assert res[1]["state"] == "minimize"

    res2 = parse_window_state_directive("Maximize Chrome")
    assert res2 is not None
    assert res2[1]["state"] == "maximize"
    assert res2[1]["target"] == "chrome"


def test_compound_directive_detection():
    # Single action
    assert MultiStepPlanner.is_compound_directive("Open Spotify") is False
    assert MultiStepPlanner.is_compound_directive("What is the weather today?") is False

    # Multi-step action
    compound = "Open Spotify, play my study playlist, and minimize the window"
    assert MultiStepPlanner.is_compound_directive(compound) is True

    steps = MultiStepPlanner.parse_plan(compound)
    assert len(steps) >= 3
    assert "open spotify" in steps[0].instruction.lower()
    assert "play" in steps[1].instruction.lower()
    assert "minimize" in steps[2].instruction.lower()


def test_spotify_metadata_lookup():
    meta = resolve_track_metadata("Believer Imagine Dragons")
    assert meta["title"] != ""
    assert "believer" in meta["title"].lower()
    assert "imagine dragons" in meta["artist"].lower()
    assert meta["verified"] is True


def test_exact_volume_control():
    # Query current volume
    curr = control_volume("get")
    assert curr["success"] is True
    assert "level" in curr

    # Calibrate to exact level 75%
    set_res = control_volume("set", level=75)
    assert set_res["success"] is True
    assert set_res["level"] == 75

    # Media controls
    med = control_media("play_pause")
    assert med["success"] is True


def test_file_operations_and_search(tmp_path):
    # Create folder in tmp
    test_folder = tmp_path / "College Projects"
    res = create_directory("College Projects", parent_folder=str(tmp_path))
    assert res["success"] is True
    assert test_folder.exists()

    # Search in tmp
    test_file = test_folder / "cybersecurity_report.pdf"
    test_file.write_text("JARVIS test document")
    
    search_res = search_files(query="cybersecurity", base_dir=str(test_folder), extension=".pdf")
    assert search_res["success"] is True
    assert search_res["count"] >= 1
    assert "cybersecurity_report.pdf" in search_res["files"][0]["name"]


@pytest.mark.asyncio
async def test_gemini_doubt_resolution():
    """Verify Gemini AI solves doubts accurately with persona and no step breakdown."""
    from app.ai.provider import get_ai_provider
    provider = get_ai_provider()
    
    query = [{"role": "user", "content": "Explain what is an API in 2 sentences."}]
    res = await provider.chat(query)
    
    assert res.status == "success"
    assert "Step 1" not in res.message
    assert "interface" in res.message.lower() or "application" in res.message.lower() or "software" in res.message.lower()
    assert len(res.tool_calls) == 0


@pytest.mark.asyncio
async def test_simultaneous_command_and_doubt():
    """Verify simultaneous execution of desktop commands while solving user doubts."""
    from app.ai.provider import get_ai_provider
    provider = get_ai_provider()
    
    query = [{"role": "user", "content": "Open Notepad and summarize what is a compiler in 1 sentence."}]
    res = await provider.chat(query)
    
    assert res.status == "success"
    assert "Step 1" not in res.message
    assert any(t.name in ["open_approved_app", "launch_custom_application"] for t in res.tool_calls)
    assert "compiler" in res.message.lower() or "code" in res.message.lower() or "machine" in res.message.lower() or "program" in res.message.lower()
