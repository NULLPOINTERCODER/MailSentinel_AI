import pytest
from httpx import ASGITransport, AsyncClient
from app.main import create_app
from app.core.logging_config import SENSITIVE_PATTERNS


@pytest.mark.asyncio
async def test_security_headers_and_request_id():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        
        # Verify security hardening headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        
        # Verify telemetry headers
        assert "X-Request-ID" in response.headers
        assert "X-Response-Time-Ms" in response.headers


def test_sensitive_log_filter():
    test_msg = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz and api_key='gsk_1234567890abcdef' password='mySecretPassword123'"
    
    cleaned = test_msg
    for pattern, repl in SENSITIVE_PATTERNS:
        cleaned = pattern.sub(repl, cleaned)
        
    assert "mySecretPassword123" not in cleaned
    assert "gsk_1234567890abcdef" not in cleaned
    assert "[REDACTED]" in cleaned
