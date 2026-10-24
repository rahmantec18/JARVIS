import pytest
from httpx import AsyncClient, ASGITransport
from desktop_agent.app.main import app
from desktop_agent.security.authorizer import authorizer

TOKEN = authorizer.config.get("auth_token", "jarvis-desktop-secret-token-change-in-production")
AUTH_HEADER = {"Authorization": f"Bearer {TOKEN}"}


@pytest.mark.asyncio
async def test_desktop_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "online"


@pytest.mark.asyncio
async def test_desktop_auth_enforcement():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Without auth header
        unauth = await client.get("/api/status")
        assert unauth.status_code == 401

        # With invalid token
        invalid = await client.get("/api/status", headers={"Authorization": "Bearer bad-token"})
        assert invalid.status_code == 401

        # With valid token
        valid = await client.get("/api/status", headers=AUTH_HEADER)
        assert valid.status_code == 200
        assert valid.json()["status"] == "connected"


@pytest.mark.asyncio
async def test_reject_unauthorized_application():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/action", headers=AUTH_HEADER, json={
            "action": "launch_app",
            "parameters": {"app_id": "malicious_ransomware"}
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "not in the authorized desktop allowlist" in data["error"]


@pytest.mark.asyncio
async def test_url_scheme_validation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Reject unsafe scheme
        unsafe = await client.post("/api/action", headers=AUTH_HEADER, json={
            "action": "open_url",
            "parameters": {"url": "javascript:alert(1)"}
        })
        assert unsafe.status_code == 200
        assert unsafe.json()["success"] is False
        assert "only http:// and https://" in unsafe.json()["error"]


@pytest.mark.asyncio
async def test_sensitive_app_requires_approval():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 'cmd' requires approval
        resp = await client.post("/api/action", headers=AUTH_HEADER, json={
            "action": "launch_app",
            "parameters": {"app_id": "cmd"},
            "confirmed": False
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["requires_confirmation"] is True
        assert "approval_id" in data

        # Resolve approval with rejection
        approval_id = data["approval_id"]
        reject_resp = await client.post(f"/api/approve/{approval_id}", headers=AUTH_HEADER, json={"approved": False})
        assert reject_resp.status_code == 200
        assert reject_resp.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_system_info_telemetry():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/action", headers=AUTH_HEADER, json={
            "action": "system_info"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "cpu_percent" in data["data"]
        assert "memory_percent" in data["data"]
