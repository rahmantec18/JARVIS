import pytest
from app.tools.calculator import calculate
from app.tools.system_status import get_system_status
from app.tools.registry import tool_registry
from app.tools.file_ops import search_allowed_files, read_selected_file, create_note


def test_calculator_basic():
    res = calculate("25 * 4 + 10")
    assert res.get("result") == 110


def test_calculator_advanced():
    res = calculate("sqrt(144) + 8")
    assert res.get("result") == 20.0


def test_calculator_syntax_error():
    res = calculate("invalid_var * 2")
    assert "error" in res


def test_system_status():
    status = get_system_status()
    assert "cpu" in status
    assert "memory" in status
    assert "os" in status
    assert "uptime" in status
    assert status["cpu"]["percent"] >= 0


def test_tool_registry():
    tools = tool_registry.list_tools()
    tool_names = [t.name for t in tools]
    assert "calculate" in tool_names
    assert "get_system_status" in tool_names
    assert "search_web" in tool_names
    assert "open_approved_app" in tool_names


@pytest.mark.asyncio
async def test_tool_registry_execution():
    res = await tool_registry.execute("calculate", {"expression": "100 / 4"})
    assert res.success is True
    assert res.result["result"] == 25.0


def test_file_ops_isolation(tmp_path):
    # Test directory isolation
    search_res = search_allowed_files("nonexistent_test_query")
    assert search_res["success"] is True

    # Note creation
    note_res = create_note("Test Title", "Test Content")
    assert note_res["success"] is True
