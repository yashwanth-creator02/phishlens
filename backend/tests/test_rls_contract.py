from __future__ import annotations

import os
import pytest
import httpx

@pytest.fixture
def supabase_config():
    url = os.getenv("SUPABASE_URL")
    anon = os.getenv("SUPABASE_ANON_KEY", os.getenv("SUPABASE_KEY", ""))
    token_a = os.getenv("USER_A_TOKEN", os.getenv("SUPABASE_USER_A_TOKEN", ""))
    token_b = os.getenv("USER_B_TOKEN", os.getenv("SUPABASE_USER_B_TOKEN", ""))
    analysis_b = os.getenv("ANALYSIS_B", os.getenv("SUPABASE_ANALYSIS_B", ""))
    if not url or not token_a or not token_b:
        pytest.skip("SUPABASE_URL and user JWTs not set; skipping RLS contract test against live Supabase")
    return url, anon, token_a, token_b, analysis_b

def test_rls_hides_other_users_case(supabase_config):
    url, anon, token_a, token_b, analysis_b = supabase_config
    if not analysis_b:
        pytest.skip("ANALYSIS_B not configured")
    endpoint = f"{url.rstrip('/')}/rest/v1/analyses?id=eq.{analysis_b}"
    headers = {"apikey": anon, "Authorization": f"Bearer {token_a}", "Accept": "application/json"}
    with httpx.Client() as client:
        r = client.get(endpoint, headers=headers)
        assert r.status_code == 200
        assert r.json() == []
