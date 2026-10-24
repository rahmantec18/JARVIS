import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_chat_interaction():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Chat message requesting current time
        response = await client.post("/api/chat", json={"message": "What is the time?"})
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert "message" in data
        assert data["status"] == "success"
        conv_id = data["conversation_id"]

        # Follow-up query in same conversation
        followup = await client.post("/api/chat", json={
            "conversation_id": conv_id,
            "message": "What is the system status?"
        })
        assert followup.status_code == 200
        followup_data = followup.json()
        assert followup_data["conversation_id"] == conv_id
        assert "subsystems" in followup_data["message"].lower() or "diagnostics" in followup_data["message"].lower() or "cpu" in followup_data["message"].lower()


@pytest.mark.asyncio
async def test_memory_crud():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create memory
        create_res = await client.post("/api/memory", json={
            "category": "preference",
            "key": "favorite_editor",
            "content": "Visual Studio Code with Dark Modern theme",
            "approved": True
        })
        assert create_res.status_code == 200
        mem = create_res.json()
        assert mem["key"] == "favorite_editor"
        mem_id = mem["id"]

        # List memories
        list_res = await client.get("/api/memory")
        assert list_res.status_code == 200
        items = list_res.json()
        assert any(i["id"] == mem_id for i in items)

        # Delete memory
        del_res = await client.delete(f"/api/memory/{mem_id}")
        assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_task_crud():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create task
        task_res = await client.post("/api/tasks", json={
            "title": "Calibrate holographic display",
            "priority": "high",
            "description": "Routine diagnostic calibration"
        })
        assert task_res.status_code == 200
        task_data = task_res.json()
        task_id = task_data["id"]

        # List tasks
        get_tasks = await client.get("/api/tasks")
        assert get_tasks.status_code == 200
        assert any(t["id"] == task_id for t in get_tasks.json())

        # Update task to completed
        up_res = await client.put(f"/api/tasks/{task_id}", json={"status": "completed"})
        assert up_res.status_code == 200
        assert up_res.json()["status"] == "completed"
