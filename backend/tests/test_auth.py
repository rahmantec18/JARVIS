import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.ai.provider import check_fast_path_action


@pytest.mark.asyncio
async def test_auth_rejection_invalid_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/auth/login", json={"password": "wrong_password"})
        assert resp.status_code == 401
        data = resp.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_auth_success_and_session_lifecycle():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Login with configured password "tec jarvis"
        resp = await client.post("/api/auth/login", json={"password": "tec jarvis"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        token = data["token"]
        assert token is not None

        # 2. Verify active session
        verify_resp = await client.get("/api/auth/verify", headers={"Authorization": f"Bearer {token}"})
        assert verify_resp.status_code == 200
        assert verify_resp.json()["authenticated"] is True

        # 3. Logout
        logout_resp = await client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert logout_resp.status_code == 200

        # 4. Verification after logout must fail
        post_logout_resp = await client.get("/api/auth/verify", headers={"Authorization": f"Bearer {token}"})
        assert post_logout_resp.status_code == 401


@pytest.mark.asyncio
async def test_whatsapp_and_chrome_directives():
    # Test WhatsApp messaging directive
    res_wa = await check_fast_path_action("open WhatsApp and text hi to Mom")
    assert res_wa is not None
    assert any(t.name == "send_whatsapp_message" for t in res_wa.tool_calls)
    assert "Mom" in res_wa.message

    # Test Chrome search directive
    res_ch = await check_fast_path_action("open Chrome and search for YouTube")
    assert res_ch is not None
    assert any(t.name == "open_website" for t in res_ch.tool_calls)
