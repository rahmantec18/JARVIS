import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.tools.registry import tool_registry
from app.ai.provider import MockJARVISProvider


@pytest.mark.asyncio
async def test_smart_jarvis_lore_and_capabilities():
    provider = MockJARVISProvider()

    # Test Lore / Introduction
    resp = await provider.chat([{"role": "user", "content": "Who are you?"}])
    assert "J.A.R.V.I.S." in resp.message
    assert resp.status == "success"

    # Test Stark / Iron Man reference
    resp_stark = await provider.chat([{"role": "user", "content": "Protocol Mark 85 ready?"}])
    assert "protocol" in resp_stark.message.lower() or "mark" in resp_stark.message.lower()

    # Test Help / Capabilities
    resp_help = await provider.chat([{"role": "user", "content": "What can you do?"}])
    assert "Desktop App Launching" in resp_help.message or "PowerShell" in resp_help.message


@pytest.mark.asyncio
async def test_smart_jarvis_tool_dispatch():
    provider = MockJARVISProvider()

    # Test Volume
    resp_vol = await provider.chat([{"role": "user", "content": "Mute volume"}])
    assert any(t.name == "control_system_volume" for t in resp_vol.tool_calls)

    # Test Calculator
    resp_calc = await provider.chat([{"role": "user", "content": "Calculate 2048 * 4"}])
    assert any(t.name == "calculate" for t in resp_calc.tool_calls)

    # Test Time
    resp_time = await provider.chat([{"role": "user", "content": "What is the time?"}])
    assert any(t.name == "get_current_time" for t in resp_time.tool_calls)


@pytest.mark.asyncio
async def test_new_tools_registered():
    tools = tool_registry.list_tools()
    names = [t.name for t in tools]
    assert "run_powershell_command" in names
    assert "control_system_volume" in names
    assert "capture_desktop_screenshot" in names
    assert "read_system_clipboard" in names
    assert "write_system_clipboard" in names
    assert "list_system_processes" in names
    assert "kill_system_process" in names
    assert "lock_windows_workstation" in names
    assert "launch_custom_application" in names


@pytest.mark.asyncio
async def test_fast_path_whatsapp_and_apps():
    from app.ai.provider import check_fast_path_action
    
    # Test fast-path whatsapp
    resp_wa = await check_fast_path_action("open whatsapp")
    assert resp_wa is not None
    assert any(t.name in ["open_approved_app", "launch_custom_application"] for t in resp_wa.tool_calls)
    assert "whatsapp" in resp_wa.message.lower()

    # Test fast-path chrome
    resp_ch = await check_fast_path_action("open chrome")
    assert resp_ch is not None
    assert any(t.name == "open_approved_app" for t in resp_ch.tool_calls)

    # Test fast-path volume up
    resp_vol = await check_fast_path_action("volume up")
    assert resp_vol is not None
    assert any(t.name == "control_system_volume" for t in resp_vol.tool_calls)

    # Non-action question should return None to let LLM handle it
    resp_qa = await check_fast_path_action("Explain quantum mechanics in detail")
    assert resp_qa is None


@pytest.mark.asyncio
async def test_root_dual_mode_serving():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # JSON API request
        json_resp = await client.get("/", headers={"Accept": "application/json"})
        assert json_resp.status_code == 200
        assert json_resp.json()["status"] == "online"

        # Browser HTML request
        html_resp = await client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
        assert html_resp.status_code == 200
        assert "text/html" in html_resp.headers.get("content-type", "")
